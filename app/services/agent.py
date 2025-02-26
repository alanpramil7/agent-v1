from app.core.config import settings
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.tools.base import BaseTool
from langchain_core.tools import tool
from app.services.react_agent import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any

from app.utils.logger import logger
from app.services.indexer import IndexerService


class AgentService:
    def __init__(self, indexer: IndexerService):
        self.llm = settings.llm
        self.indexer = indexer
        self.db = SQLDatabase.from_uri(settings.database)
        self.sql_toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.sql_tools = self.sql_toolkit.get_tools()
        self.retriver_tool = self._create_retriver_tool()
        self.tools = self.sql_tools + [self.retriver_tool]

        self.memory = MemorySaver()
        self.agent_executor = self._create_agent()

    def _create_retriver_tool(self) -> BaseTool:
        @tool
        async def retrive_documents(query: str):
            """
            Retrieve relevant documents from the vector store based on the query.
            Use this tool when you need to find information from documents rather than from the database.

            Args:
                query (str): The search query to find relevant documents

            Returns:
                str: Concatenated content from relevant documents
            """
            logger.debug(f"Retriving docs for query: {query}")

            if not self.indexer.vector_store:
                raise ValueError("Vector store is undefined.")

            retriver = self.indexer.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5},
            )

            docs = await retriver.ainvoke(query)

            if not docs:
                return "No documents are found."

            for i, doc in enumerate(docs):
                logger.debug(f"Retrieved document {i}: {doc.page_content[:100]}...")

            context = "\n\n".join(
                [f"Document {i + 1}:\n{doc.page_content}" for i, doc in enumerate(docs)]
            )

            return context

        return retrive_documents

    def _create_agent(self):
        """Create a LangGraph agent with the configured tools."""
        system_message = """You are a helpful and knowledgeable assistant with access to various tools. Your goal is to provide accurate and helpful responses to user questions by using the appropriate tools.

**You have access to the following tools:**
1. **SQL Database Tools**
2. **Document Retrieval Tool**

**When using SQL tools:**
- Always start by exploring the available tables using the `sql_db_list_tables` tool.
- Then examine the schema of relevant tables using the `sql_db_schema` tool.
- Finally, use `sql_db_query` to run a query and get the answer.
- **DO NOT** make any DML statements (INSERT, UPDATE, DELETE, DROP, etc.) to the database.
- Craft queries to select only the necessary columns and rows; avoid fetching all content unless explicitly required by the question.
- **Important:** Ensure that the query is crafted using the exact column names, data types, and table relationships from the schema. Do not assume the schema; always base the query on the retrieved information.
- Verify that the query aligns with the schema to avoid errors (e.g., incorrect column names or data types).
- If the schema does not match expectations or if there are errors, adjust the query accordingly or inform the user of any discrepancies.
- Use `WHERE` clauses to filter data based on the question's criteria.
- Utilize aggregate functions (e.g., `SUM`, `AVG`, `COUNT`) for calculations like total cost, average usage, etc., instead of retrieving raw data and computing manually.
- Avoid using `SELECT *` unless the question explicitly requires all columns.
- Aim to make your queries efficient, retrieving only the data needed to answer the question.

**When using the document retrieval tool:**
- Use clear, specific queries to find the most relevant documents.
- Synthesize information from multiple documents when needed.

**Important guidelines:**
- Choose the appropriate tool based on the nature of the question:
  - For questions requiring specific data points, calculations, or statistics from the database—especially related to Azure cloud data—use the **SQL tools**.
  - For questions seeking general knowledge, explanations, or information not specific to the database, use the **document retrieval tool**.
- If the question requires both specific data and general knowledge, use both tools and combine the information in your response.
- Always provide clear, concise responses based on the information obtained from the tools.
- Never claim to know information that isn't provided by the tools. If you don't have enough information, say so clearly and suggest how the user might refine their question.

**Note:** The database contains data related to Azure cloud services, including costs, resource usage, and other metrics. Therefore, questions about Azure data (e.g., costs, usage statistics) should primarily be answered using the SQL tools.
"""

        agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_message,
            checkpointer=self.memory,
        )

        return agent

    async def process_question(
        self, question: str, thread_id: str = None
    ) -> Dict[str, Any]:
        """
        Process a user question using the LangGraph agent.

        Args:
            question: The user's question
            thread_id: Optional thread ID for maintaining conversation context

        Returns:
            Dict containing the agent's response and any relevant metadata
        """
        logger.debug(f"Processing question: {question}")

        if not thread_id:
            thread_id = "default"

        config = {"configurable": {"thread_id": thread_id}}

        try:
            messages = [("human", question)]

            result = await self.agent_executor.ainvoke({"messages": messages}, config)

            final_answer = result["messages"][-1].content

            return final_answer

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question.",
                "status": "error",
                "error": str(e),
            }

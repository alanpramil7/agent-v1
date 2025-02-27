"""
Agent Service Module

This module provides an agent service that processes user questions using LangChain components,
SQL database tools, and document retrieval capabilities.
"""

from typing import Any, AsyncGenerator, Optional

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.tools import tool
from langchain_core.tools.base import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from rich import print

from app.core.config import settings
from app.services.indexer import IndexerService
from app.services.react_agent import create_react_agent
from app.utils.logger import logger


class AgentService:
    """
    Agent service for processing user questions using a combination of LLM,
    SQL tools, and document retrieval capabilities.

    This class orchestrates the interaction between different components to provide
    accurate and helpful responses to user questions.
    """

    def __init__(self, indexer: IndexerService) -> None:
        """
        Initialize the Agent Service with necessary components.

        Args:
            indexer (IndexerService): Service for document indexing and retrieval
        """
        # Initialize the language model from settings
        self.llm = settings.llm
        self.indexer = indexer

        # Set up SQL database connection and tools
        self.db = SQLDatabase.from_uri(settings.database)
        self.sql_toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.sql_tools = self.sql_toolkit.get_tools()

        # Create document retriever tool
        self.retriver_tool = self._create_retriver_tool()

        # Combine all tools
        self.tools = self.sql_tools + [self.retriver_tool]

        # Create the agent executor
        self.memory = MemorySaver()
        self.agent_executor = self._create_agent()

    def _create_retriver_tool(self) -> BaseTool:
        """
        Create a document retrieval tool that can fetch relevant documents
        from the vector store based on a query.

        Returns:
            BaseTool: The document retrieval tool
        """

        @tool
        async def retrive_documents(query: str) -> str:
            """
            Retrieve relevant documents from the vector store based on the query.
            Use this tool when you need to find information from documents rather than from the database.

            Args:
                query (str): The search query to find relevant documents

            Returns:
                str: Concatenated content from relevant documents
            """
            logger.debug(f"Retriving docs for query: {query}")

            # Validate vector store existence
            if not self.indexer.vector_store:
                raise ValueError("Vector store is undefined.")

            # Configure retriever with similarity search
            retriver = self.indexer.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5},  # Retrieve top 5 relevant documents
            )

            # Retrieve documents based on the query
            docs = await retriver.ainvoke(query)

            if not docs:
                return "No documents are found."

            # Log retrieved documents for debugging
            for i, doc in enumerate(docs):
                logger.debug(f"Retrieved document {i}: {doc.page_content[:100]}...")

            # Format documents into a readable context string
            context = "\n\n".join(
                [f"Document {i + 1}:\n{doc.page_content}" for i, doc in enumerate(docs)]
            )

            return context

        return retrive_documents

    def _create_agent(self):
        """
        Create a LangGraph agent with the configured tools and system prompt.

        Returns:
            Agent executor that can process user questions
        """
        # Comprehensive system message that guides the agent's behavior
        system_message = """You are a helpful and knowledgeable assistant with access to various tools. Your goal is to provide accurate and helpful responses to user questions by using the appropriate tools.

**You have access to the following tools:**
1. **SQL Database Tools**
2. **Document Retrieval Tool**

**When using SQL tools:**
- Always start by exploring the available tables using the `sql_db_list_tables` tool. Select one or more tables that might have any relation to user question.
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
        self, question: str, thread_id: Optional[str] = None
    ) -> Any:
        """
        Process a user question using the LangGraph agent.

        Args:
            question (str): The user's question
            thread_id (Optional[str]): Thread ID for maintaining conversation context

        Returns:
            The agent's response or error information
        """
        logger.debug(f"Processing question: {question}")

        # Use default thread_id if none provided
        if not thread_id:
            thread_id = "default"

        # Configure the thread ID for the agent
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 10}

        try:
            # Format the question as a message for the agent
            messages = [("human", question)]

            # Invoke the agent with the message
            result = await self.agent_executor.ainvoke({"messages": messages}, config)

            # Extract the final answer from the agent's response
            final_answer = result["messages"][-1].content

            return final_answer

        except Exception as e:
            # Log and handle any errors that occur during processing
            logger.error(f"Error processing question: {str(e)}")
            return {
                "answer": "I apologize, but I encountered an error while processing your question.",
                "status": "error",
                "error": str(e),
            }

    async def stream_question(
        self, question: str, thread_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a user question using the LangGraph agent.

        This method allows for returning the agent's response as chunks in real-time,
        rather than waiting for the entire response to be generated.

        Args:
            question (str): The user's question
            thread_id (Optional[str]): Thread ID for maintaining conversation context

        Yields:
            str: Chunks of the agent's response
        """
        logger.debug(f"Streaming response for question: {question}")

        # Use default thread_id if none provided
        if not thread_id:
            thread_id = "default"

        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 10}

        try:
            # Format the question as a message for the agent
            messages = [("human", question)]

            # Stream the agent's response
            async for event in self.agent_executor.astream(
                {"messages": messages}, config
            ):
                # Debug: print(event)
                if "agent" in event:
                    for message in event["agent"]["messages"]:
                        print(message.content)
                        yield message.content + "\n"

        except Exception as e:
            # Log and handle any errors that occur during streaming
            logger.error(f"Error streaming question: {str(e)}")
            yield "I encountered an error while processing your question.\n"

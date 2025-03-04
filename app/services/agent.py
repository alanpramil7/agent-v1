"""
Agent Service Module

This module provides an agent service that processes user questions using LangChain components,
SQL database tools, and document retrieval capabilities.
"""

import json
from typing import Any, AsyncGenerator, Optional
import uuid

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.tools.base import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from rich import print

from app.core.config import settings
from app.services.database import DatabaseService
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

    def __init__(self, indexer: IndexerService, database: DatabaseService) -> None:
        """
        Initialize the Agent Service with necessary components.

        Args:
            indexer (IndexerService): Service for document indexing and retrieval
        """
        # Initialize the language model from settings
        self.llm = settings.llm
        self.indexer = indexer
        self.database = database

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
                logger.debug(f"Retrieved document {i}: {doc}")

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
        system_message = """You are a helpful and knowledgeable assistant with access to tools to provide accurate and concise answers to user questions.

### Available Tools
- **SQL Database Tools**: For querying specific data points, calculations, or statistics from the database, especially Azure cloud data (e.g., costs, resource usage).
- **Document Retrieval Tool**: For general knowledge, explanations, or information not specific to the database.

### Tool Selection Guide
- Use **SQL tools** for questions like:
  - "What is the total cost of Azure services last month?"
  - "How many resources are active in my Azure subscription?"
- Use the **document retrieval tool** for questions like:
  - "What is Azure?"
  - "How does cloud computing work?"
- For questions needing both (e.g., "Explain the cost breakdown of my Azure services"), use both tools and combine the results.

### Using SQL Tools
**IMPORTANT**: Don't use recommendation table for sql related questions unless and until it is necessary or requested by user.
1. **List Tables**: Use `sql_db_list_tables` to identify available tables related to the question.
2. **Check Schema**: Use `sql_db_schema` on relevant tables to understand their structure.
3. **Write Query**:
   - Enclose column names in double quotes (e.g., `"column_name"`).
   - Use **LIMIT 10** statement always unless and until you need all data to do calculations.
   - Use exact column names and data types from the schema—do not assume.
   - Select only necessary columns and rows; avoid `SELECT *` unless required.
   - Apply `WHERE` clauses to filter data and aggregate functions (e.g., `SUM`, `AVG`, `COUNT`) for calculations.
   - **DO NOT** use DML statements (INSERT, UPDATE, DELETE, DROP, etc.).
4. **Execute**: Run the query with `sql_db_query`, ensuring it matches the schema to avoid errors.
5. **Errors**: If the query fails or data is missing, inform the user and suggest refining the question.

### Using Document Retrieval Tool
- Submit clear, specific queries to retrieve relevant documents.
- Combine information from multiple documents if needed for a complete answer.

### General Guidelines
- Provide concise, accurate responses based solely on tool outputs.
- If information is insufficient, say so and suggest how the user might refine their question.
- Do not invent information not provided by the tools.
- Maintain a professional, helpful tone, especially when addressing limitations.

### Combining Tools
- For mixed questions, fetch specific data with SQL tools first, then supplement with document retrieval insights.
- Ensure the response is cohesive and fully answers the question.

### Note
The database contains Azure cloud service data (e.g., costs, usage metrics). Prioritize SQL tools for Azure-related questions."""

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
        self,
        user_id: str,
        conversation_id: str,
        question: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a user question using the LangGraph agent.

        This method allows for returning the agent's response as chunks in real-time,
        rather than waiting for the entire response to be generated.

        Args:
            user_id (str): The user's ID
            conversation_id (Optional[str]): Conversation ID for maintaining conversation context
            question (str): The user's question

        Yields:
            str: Chunks of the agent's response
        """
        logger.debug(f"Streaming response for question: {question}")

        # Use default thread_id if none provided
        if not conversation_id:
            conversation_id = "default"

        config = {"configurable": {"thread_id": conversation_id}, "recursion_limit": 25}

        # Add conversation to database
        if not self.database.conversation_exists(conversation_id):
            self.database.add_conversation(conversation_id, user_id)

        try:
            # Format the question as a message for the agent
            messages = [("human", question)]

            # Add user message to database
            user_message_id = str(uuid.uuid4())
            self.database.add_message(
                user_message_id, conversation_id, "user", question
            )

            # Create a single message ID for the AI response
            ai_message_id = str(uuid.uuid4())
            complete_message = ""

            async for current_message, metadata in self.agent_executor.astream(
                {"messages": messages}, config, stream_mode="messages"
            ):
                if isinstance(current_message, ToolMessage):
                    # Yield tool message immediately
                    tool_message = {
                        "type": "tool_message",
                        "content": current_message.content,
                        "tool_call_id": current_message.tool_call_id,
                        "tool_name": current_message.name,
                    }
                    yield json.dumps(tool_message) + "\n"
                    self.database.add_message(
                        current_message.id,
                        conversation_id,
                        "tool message",
                        tool_message,
                    )

                if isinstance(current_message, AIMessage):
                    # Stream agent content deltas
                    if current_message.content:  # Only yield if the chunk has content
                        delta_message = {
                            "type": "agent_message_delta",
                            "delta": current_message.content,
                        }
                        logger.debug(current_message.content)
                        complete_message += current_message.content
                        yield json.dumps(delta_message) + "\n"
                    if current_message.response_metadata.get("finish_reason") == "stop":
                        logger.debug("Completed.")
                        # Signal completion
                        completion_message = {"type": "agent_message_complete"}
                        yield json.dumps(completion_message) + "\n"
                        # Only add the complete message to database if it's not empty
                        if complete_message.strip():
                            self.database.add_message(
                                ai_message_id,
                                conversation_id,
                                "ai",
                                complete_message,
                            )

        except Exception as e:
            logger.error(f"Error streaming question: {str(e)}")
            yield "I encountered an error while processing your question.\n"

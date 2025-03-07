import json
from typing import AsyncGenerator

from langchain_core.messages import AIMessage, ToolMessage

from app.core.config import settings
from app.services.indexer import IndexerService
from app.services.memory import MemoryService
from app.services.retrival_agent import RetrievalAgent
from app.services.sql_agent import SqlAgent
from app.utils.logger import logger


class AgentService:
    """
    Agent service for orchestrating multiple specialized agents to process user questions.
    This service determines which agent to use based on the question type.
    """

    def __init__(
        self,
        indexer: IndexerService,
        memory: MemoryService,
    ) -> None:
        """
        Initialize the Agent Service with necessary components.

        Args:
            indexer (IndexerService): Service for document indexing and retrieval
            memory (MemoryService): Service for maintaining conversation context
        """
        # Initialize the language model from settings
        self.llm = settings.llm
        self.indexer = indexer
        self.memory = memory

        # Create specialized agents
        self.doc_agent = RetrievalAgent(indexer=indexer)
        self.sql_agent = SqlAgent()

    async def _classify_query(self, query: str) -> str:
        """
        Determine whether to use SQL or Document Retrieval.

        Args:
            query (str): The user's query to classify

        Returns:
            str: 'SQL' or 'DOCS' depending on the classification
        """
        prompt = (
            f"Analyze this query: '{query}'\n\n"
            f"If it requires database access (specific data, calculations, statistics, "
            f"or any information that would be stored in a database related to "
            f"Azure cloud data like costs or resource usage), respond with 'SQL'.\n"
            f"If it requires information from documents (explanations, concepts, "
            f"processes, general knowledge), respond with 'DOCS'.\n\n"
            f"Response (SQL or DOCS only):"
        )

        response = await self.llm.ainvoke(prompt)
        return "SQL" if "SQL" in response.content.upper() else "DOCS"

    async def _get_agent_for_type(self, agent_type: str):
        """
        Return the appropriate agent based on classification.

        Args:
            agent_type (str): 'SQL' or 'DOCS'

        Returns:
            An initialized agent ready to process the query
        """
        if agent_type == "SQL":
            return await self.sql_agent.create_sql_agent(self.memory)
        else:
            return await self.doc_agent.create_retrieval_agent(self.memory)

    async def stream_question(
        self,
        user_id: str,
        conversation_id: str,
        question: str,
    ) -> AsyncGenerator[str, None]:
        """
        Process a user question and stream the response from the appropriate agent.

        Args:
            user_id (str): The ID of the user asking the question
            conversation_id (str): The ID of the current conversation
            question (str): The user's question to be answered

        Yields:
            str: JSON-formatted chunks of the response
        """
        logger.debug(f"Processing question: {question}")

        if not conversation_id:
            conversation_id = "default"

        try:
            # Determine agent type
            agent_type = await self._classify_query(question)
            logger.info(f"Selected agent type: {agent_type} for query: {question}")

            # Provide feedback on which agent is being used
            # routing_message = {
            #     "type": "agent_message_delta",
            #     "delta": f"Based on your question, I'll {'use the database' if agent_type == 'SQL' else 'search relevant documents'} to find an answer.\n\n",
            # }
            # yield f"data: {json.dumps(routing_message)}\n\n"

            # Get the appropriate agent
            agent = await self._get_agent_for_type(agent_type)

            # Stream the agent's response
            config = {
                "configurable": {"thread_id": conversation_id},
                "recursion_limit": 25,
            }
            messages = [("human", question)]
            complete_message = ""

            async for current_message, metadata in agent.astream(
                {"messages": messages}, config, stream_mode="messages"
            ):
                # print(current_message)
                # Handle tool messages (showing intermediate reasoning)
                if isinstance(current_message, ToolMessage):
                    tool_message = {
                        "type": "tool_message",
                        "content": current_message.content,
                        "tool_call_id": current_message.tool_call_id,
                        "tool_name": current_message.name,
                    }
                    yield f"data: {json.dumps(tool_message)}\n\n"

                # Handle AI messages (the actual response)
                if isinstance(current_message, AIMessage) and current_message.content:
                    delta_message = {
                        "type": "agent_message_delta",
                        "delta": current_message.content,
                    }
                    complete_message += current_message.content
                    yield f"data: {json.dumps(delta_message)}\n\n"

                    # Signal completion
                    if (
                        current_message.response_metadata
                        and current_message.response_metadata.get("finish_reason")
                        == "stop"
                    ):
                        completion_message = {"type": "agent_message_complete"}
                        yield f"data: {json.dumps(completion_message)}\n\n"
                        if complete_message.strip():
                            logger.debug(f"Complete response: {complete_message}")

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            error_message = {
                "type": "agent_message_delta",
                "delta": f"I encountered an error while processing your question: {str(e)}",
            }
            yield f"data: {json.dumps(error_message)}\n\n"

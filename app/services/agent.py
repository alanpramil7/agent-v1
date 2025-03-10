import json
from typing import AsyncGenerator, Dict, List

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

    async def _classify_query(
        self,
        query: str,
    ) -> str:
        """
        Determine whether to use SQL or Document Retrieval based on the query

        Args:
            query (str): The user's query to classify.

        Returns:
            str: 'SQL' or 'DOCS' depending on the classification.
        """
        prompt = (
            f"Determine the appropriate response type based on the query: {query}\n"
            "If the query is about optimizing cloud costs, always use 'SQL'.\n"
            "If the query requires database access, such as retrieving, calculating, or analyzing data (e.g., costs, resource usage, or statistical analysis), respond with 'SQL'.\n"
            "Always return 'SQL' if the query involves calculations and requires data from a database.\n"
            "If the query is related to Amadis or Cloudcadi, respond with 'DOCS'.\n"
            "If the query requires conceptual knowledge, explanations, or information from documents, respond with 'DOCS'.\n"
            "Response (SQL or DOCS only):"
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
            # history = await self.memory.get_conversation_history(conversation_id)
            # history = self.extract_all_messages(history)
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

    def extract_all_messages(self, history: List[Dict]) -> List[Dict[str, str]]:
        """
        Process the raw conversation history and extract all human and AI messages,
        preserving their chronological order.

        Returns:
            List[Dict[str, str]]: A list of dictionaries with keys "role" and "content".
        """
        messages = []
        for checkpoint in history:
            metadata = checkpoint.get("metadata") or {}
            source = metadata.get("source", "")
            writes = metadata.get("writes") or {}

            if source == "input":
                # Extract human messages from checkpoints with source "input"
                start_writes = writes.get("__start__") or {}
                msg_list = start_writes.get("messages") or []
                for item in msg_list:
                    # Expecting each item to be a list like: [role, content]
                    if isinstance(item, list) and len(item) >= 2:
                        role, content = item[0], item[1]
                        if isinstance(role, str) and role.lower() == "human":
                            messages.append({"role": "human", "content": content})
            elif source == "loop":
                # Extract AI messages from checkpoints with source "loop"
                agent_writes = writes.get("agent") or {}
                msg_list = agent_writes.get("messages") or []
                for msg in msg_list:
                    if isinstance(msg, dict):
                        kwargs = msg.get("kwargs") or {}
                        content = kwargs.get("content")
                        if content:
                            messages.append({"role": "ai", "content": content})
        return messages

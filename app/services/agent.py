import functools
import json
from typing import (
    AsyncGenerator,
    Literal,
    Union,
)

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from rich import print

from app.core.config import settings
from app.models.agentstate import AgentState
from app.services.indexer import IndexerService
from app.services.memory import MemoryService
from app.services.retrival_agent import RetrievalAgent
from app.services.sql_agent import SqlAgent
from app.utils.logger import logger


class RouteResponse(BaseModel):
    """Structured output for the supervisor's routing decision."""

    next: Union[Literal["FINISH"], Literal["SQL_agent"], Literal["DOCS_agent"]]


class AgentService:
    """
    Agent service for orchestrating multiple specialized agents using a LangGraph workflow.
    A supervisor agent routes queries to either an SQL agent or a document retrieval agent.
    """

    def __init__(
        self,
        indexer: IndexerService,
        memory: MemoryService,
    ) -> None:
        """
        Initialize the Agent Service with necessary components and set up the workflow.

        Args:
            indexer (IndexerService): Service for document indexing and retrieval
            memory (MemoryService): Service for maintaining conversation context
        """
        self.llm = settings.llm
        self.indexer = indexer
        self.memory = memory

        # Create specialized agents
        self.doc_agent = RetrievalAgent(indexer=indexer)
        self.sql_agent = SqlAgent()

        # Set up the LangGraph workflow
        self.graph = None

    async def ainit(self):
        """Asynchronously initialize the service by setting up the workflow graph."""
        checkpointer = await self.memory.get_memory_saver()
        self.graph = await self._create_workflow(checkpointer)

    async def _create_workflow(self, checkpointer):
        """
        Create and compile the LangGraph workflow with supervisor and agent nodes.

        Returns:
            Compiled LangGraph workflow
        """
        members = ["SQL_agent", "DOCS_agent"]
        options = ["FINISH"] + members

        # Define the supervisor prompt
        supervisor_prompt = """
You are a supervisor tasked with managing a conversation between the following workers: {members}. Given the user request and conversation history, respond with the worker to act next.
Each worker will perform a task and report back.
If the conversation is over, respond with 'FINISH'.

- **SQL_agent**: Use this worker for tasks that involve:
  - Optimizing cloud costs.
  - Providing recommendations on cloud usage.
  - Analyzing cloud cost and performing calculations.
  - Retrieving, calculating, or analyzing data from the database.

- **DOCS_agent**: Use this worker for tasks that involve:
  - Questions related to Amadis or Cloudcadi.
  - Conceptual knowledge, explanations, or information from documents.

Decision Criteria:
- If the query is about cloud costs, usage, or requires database access, route to **SQL_agent**.
- If the query is about Amadis, Cloudcadi, or requires document information, route to **DOCS_agent**.
- If the query is a general greeting or doesn’t require specific agent capabilities, respond directly.

Example Decision Flow:
- Query: "How can I reduce my AWS costs?" -> **SQL_agent**
- Query: "What is Amadis?" -> **DOCS_agent**
- Query: "Hello" -> Respond directly

Based on the conversation, who should act next? Or should we FINISH? Select one of: {options}
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", supervisor_prompt),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    "Given the conversation above, who should act next? Or should we FINISH? Select one of: {options}",
                ),
            ]
        ).partial(options=str(options), members=", ".join(members))

        # Define the supervisor chain
        supervisor_chain = prompt | self.llm.with_structured_output(RouteResponse)

        def supervisor_agent(state):
            """Supervisor node that decides the next agent."""
            logger.debug("Calling supervisor node.")
            route_response = supervisor_chain.invoke(state)
            return {"next": route_response.next}

        # Define agent node function
        async def agent_node(state, agent, name):
            """Invoke an agent and update the state with its response."""
            logger.debug(f"Calling agent node with agent: {agent}")
            result = await agent.ainvoke({"messages": state["messages"]})
            last_message = result["messages"][-1]
            return {"messages": [AIMessage(content=last_message.content, name=name)]}

        doc_agent_instance = await self.doc_agent.create_retrieval_agent(self.memory)
        sql_agent_instance = await self.sql_agent.create_sql_agent(self.memory)

        # Create agent nodes
        doc_node = functools.partial(
            agent_node, agent=doc_agent_instance, name="DOCS_agent"
        )
        sql_node = functools.partial(
            agent_node, agent=sql_agent_instance, name="SQL_agent"
        )

        # Set up the workflow
        workflow = StateGraph(AgentState)
        workflow.add_node("DOCS_agent", doc_node)
        workflow.add_node("SQL_agent", sql_node)
        workflow.add_node("supervisor", supervisor_agent)

        # Add edges
        for member in members:
            workflow.add_edge(member, "supervisor")

        conditional_map = {k: k for k in members}
        conditional_map["FINISH"] = END
        workflow.add_conditional_edges(
            "supervisor", lambda x: x["next"], conditional_map
        )

        workflow.add_edge(START, "supervisor")

        # Compile the graph with a checkpointer for conversation persistence
        return workflow.compile(checkpointer=checkpointer)

    async def stream_question(
        self,
        user_id: str,
        conversation_id: str,
        question: str,
    ) -> AsyncGenerator[str, None]:
        """
        Process a user question and stream the response using the LangGraph workflow.

        Args:
            user_id (str): The ID of the user asking the question
            conversation_id (str): The ID of the current conversatio8
            question (str): The user's question to be answered

        Yields:
            str: JSON-formatted chunks of the response
        """
        if self.graph is None:
            raise RuntimeError("Agent service is not initialized.")

        logger.debug(f"Processing question: {question}")

        if not conversation_id:
            conversation_id = "default"

        try:
            config = {
                "configurable": {"thread_id": conversation_id},
                "recursion_limit": 25,
            }
            initial_state = {"messages": [HumanMessage(content=question)]}

            async for event in self.graph.astream(
                initial_state, config, stream_mode="updates"
            ):
                print(event)
                for node, updates in event.items():
                    if node == "supervisor" and "next" in updates:
                        next_agent = updates["next"]
                        if next_agent != "FINISH":
                            routing_message = {
                                "type": "routing_message",
                                "delta": f"Routing to {'database analysis' if next_agent == 'SQL_agent' else 'document retrieval'}.\n\n",
                            }
                            yield f"data: {json.dumps(routing_message)}\n\n"
                    elif "messages" in updates:
                        for msg in updates["messages"]:
                            if isinstance(msg, AIMessage):
                                delta_message = {
                                    "type": "agent_message_delta",
                                    "delta": msg.content,
                                }
                                yield f"data: {json.dumps(delta_message)}\n\n"

            # Signal completion
            completion_message = {"type": "agent_message_complete"}
            yield f"data: {json.dumps(completion_message)}\n\n"
            logger.debug(f"Completed processing question: {question}")

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            error_message = {
                "type": "error_message",
                "delta": f"I encountered an error: {str(e)}",
            }
            yield f"data: {json.dumps(error_message)}\n\n"

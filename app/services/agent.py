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
You are a supervisor tasked with managing a conversation between the following workers: {members}.
Given the user request and conversation history, respond with the worker to act next.
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
            logger.debug(
                f"Calling supervisor node with {len(state['messages'])} message."
            )
            route_response = supervisor_chain.invoke(state)
            logger.debug(f"Routing to {route_response.next} node.")
            return {"next": route_response.next}

        # Define agent node function
        async def agent_node(state, agent, name):
            """Invoke an agent and update the state with its response."""
            logger.debug(f"Calling agent node with agent: {name}")
            result = await agent.ainvoke({"messages": state["messages"]})
            # last_message = result["messages"][-1]
            # return {"messages": [AIMessage(content=last_message.content, name=name)]}
            return {"messages": result["messages"]}

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

            async for message, metadata in self.graph.astream(
                initial_state,
                config,
                stream_mode="messages",
                debug=False,
            ):
                # Tool calls messages and metdata
                # Messge : content='\nCREATE TABLE aws_cost (\n\tid BIGSERIAL NOT NULL, \n\tdate DATE NOT NULL, \n\t"currencyCode" TEXT NOT NULL, \n\t"billType" TEXT NOT NULL, \n\t"unblendedRate" DOUBLE PRECISION, \n\t"unblendedCost" DOUBLE PRECISION,
                # \n\t"blendedRate" DOUBLE PRECISION, \n\t"blendedCost" DOUBLE PRECISION, \n\t"consumedQuantity" DOUBLE PRECISION, \n\t"payerAccountId" TEXT NOT NULL, \n\t"productCode" TEXT NOT NULL, \n\t"usageType" TEXT NOT NULL, \n\t"productFamily" TEXT,
                # \n\tsku TEXT, \n\tlocation TEXT, \n\ttags JSONB NOT NULL, \n\t"resourceId" TEXT NOT NULL, \n\t"serviceCode" TEXT, \n\t"cloudAccountId" UUID NOT NULL, \n\t"createdAt" TIMESTAMP WITH TIME ZONE NOT NULL, \n\t"updatedAt" TIMESTAMP WITH TIME
                # ZONE NOT NULL, \n\t"deletedAt" TIMESTAMP WITH TIME ZONE, \n\t"itemType" TEXT DEFAULT \'Usage\'::text NOT NULL, \n\t"usageAccountId" TEXT, \n\tCONSTRAINT aws_cost_pkey PRIMARY KEY (id)\n)\n\n/*\n3 rows from aws_cost
                # table:\nid\tdate\tcurrencyCode\tbillType\tunblendedRate\tunblendedCost\tblendedRate\tblendedCost\tconsumedQuantity\tpayerAccountId\tproductCode\tusageType\tproductFamily\tsku\tlocation\ttags\tresourceId\tserviceCode\tcloudAccountId\tcreat
                # edAt\tupdatedAt\tdeletedAt\titemType\tusageAccountId\n100944\t2023-03-20\tUSD\tAnniversary\t0.0\t0.0\t0.0\t0.0\t0.0033627283\t971650273230\tAmazonEC2\tUSE2-DataTransfer-Regional-Bytes\tData
                # Transfer\tKF338J7FCKZPUBD9\tus-east-2\t{\'Name\': \'workerenv-870032797970315-518bfc14-d09b-45e3-ae22-ff2ceb04d9e1-worker\', \'Vendor\': \'Databri\ti-0a6f493d3fddf64a2\tAWSDataTransfer\t12cecf82-448f-43ee-af8c-e9f61cbb2e8a\t2025-01-28
                # 11:24:25.995000+05:30\t2025-01-28 11:24:25.995000+05:30\tNone\tUsage\t971650273230\n100945\t2023-03-20\tUSD\tAnniversary\t0.0\t0.0\t0.0\t0.0\t0.0020273691\t971650273230\tAmazonEC2\tUSE2-DataTransfer-Regional-Bytes\tData
                # Transfer\tKF338J7FCKZPUBD9\tus-east-2\t{\'Name\': \'workerenv-870032797970315-518bfc14-d09b-45e3-ae22-ff2ceb04d9e1-worker\', \'Vendor\': \'Databri\ti-03349fc9badd9cfc4\tAWSDataTransfer\t12cecf82-448f-43ee-af8c-e9f61cbb2e8a\t2025-01-28
                # 11:24:25.995000+05:30\t2025-01-28 11:24:25.995000+05:30\tNone\tUsage\t971650273230\n100946\t2023-03-20\tUSD\tAnniversary\t0.0\t0.0\t0.0\t0.0\t0.0037171654\t971650273230\tAmazonEC2\tUSE2-DataTransfer-Regional-Bytes\tData
                # Transfer\tKF338J7FCKZPUBD9\tus-east-2\t{\'Name\': \'workerenv-870032797970315-518bfc14-d09b-45e3-ae22-ff2ceb04d9e1-worker\', \'Vendor\': \'Databri\ti-048f2ff94ed65f619\tAWSDataTransfer\t12cecf82-448f-43ee-af8c-e9f61cbb2e8a\t2025-01-28
                # 11:24:25.995000+05:30\t2025-01-28 11:24:25.995000+05:30\tNone\tUsage\t971650273230\n*/' name='sql_db_schema' id='b5dedd9e-d2e9-4028-bd62-b97c0f67cd76' tool_call_id='call_XtLbI2O6c3QCGdrc8B485d8q'
                #  Metadata : {'thread_id': '6194fedf-6088-4673-86a6-7085ba80d63d', 'langgraph_step': 4, 'langgraph_node': 'tools', 'langgraph_triggers': ['__pregel_push'], 'langgraph_path': ('__pregel_push', 0), 'langgraph_checkpoint_ns':
                # 'SQL_agent:87b687f2-a9b2-597b-ebaf-64dc88aa5fbe|tools:1bc7f496-7151-1782-75c6-f7f51e76fad4', 'checkpoint_ns': 'SQL_agent:87b687f2-a9b2-597b-ebaf-64dc88aa5fbe'}

                # Agent response message and metadata
                # Messge : content=' free' additional_kwargs={} response_metadata={} id='run-48fe0c15-9c87-42ca-8d61-b308b5511dfb'
                #  Metadata : {'thread_id': '6194fedf-6088-4673-86a6-7085ba80d63d', 'langgraph_step': 7, 'langgraph_node': 'agent', 'langgraph_triggers': ['tools'], 'langgraph_path': ('__pregel_pull', 'agent'), 'langgraph_checkpoint_ns':
                # 'SQL_agent:87b687f2-a9b2-597b-ebaf-64dc88aa5fbe|agent:3751963f-9aa0-0d9d-e089-ea99afe8c802', 'checkpoint_ns': 'SQL_agent:87b687f2-a9b2-597b-ebaf-64dc88aa5fbe', 'ls_provider': 'azure', 'ls_model_name': 'gpt-4o-mini', 'ls_model_type':
                # 'chat', 'ls_temperature': None}
                #  Messge : content=' to' additional_kwargs={} response_metadata={} id='run-48fe0c15-9c87-42ca-8d61-b308b5511dfb'
                #  Metadata : {'thread_id': '6194fedf-6088-4673-86a6-7085ba80d63d', 'langgraph_step': 7, 'langgraph_node': 'agent', 'langgraph_triggers': ['tools'], 'langgraph_path': ('__pregel_pull', 'agent'), 'langgraph_checkpoint_ns':
                # 'SQL_agent:87b687f2-a9b2-597b-ebaf-64dc88aa5fbe|agent:3751963f-9aa0-0d9d-e089-ea99afe8c802', 'checkpoint_ns': 'SQL_agent:87b687f2-a9b2-597b-ebaf-64dc88aa5fbe', 'ls_provider': 'azure', 'ls_model_name': 'gpt-4o-mini', 'ls_model_type':
                # 'chat', 'ls_temperature': None}

                # Supervisor message and metadata
                # Messge : content='' additional_kwargs={} response_metadata={} id='run-d336cc90-664d-4ebd-a90d-d7deb371283d'
                #  Metadata : {'thread_id': '6194fedf-6088-4673-86a6-7085ba80d63d', 'langgraph_step': 3, 'langgraph_node': 'supervisor', 'langgraph_triggers': ['SQL_agent'], 'langgraph_path': ('__pregel_pull', 'supervisor'), 'langgraph_checkpoint_ns':
                # 'supervisor:19bea099-f575-621d-159e-0139641e616f', 'checkpoint_ns': 'supervisor:19bea099-f575-621d-159e-0139641e616f', 'ls_provider': 'azure', 'ls_model_name': 'gpt-4o-mini', 'ls_model_type': 'chat', 'ls_temperature': None,
                # 'structured_output_format': {'kwargs': {'method': 'json_schema'}, 'schema': {'type': 'function', 'function': {'name': 'RouteResponse', 'description': "Structured output for the supervisor's routing decision.", 'parameters': {'properties':
                # {'next': {'anyOf': [{'const': 'FINISH', 'type': 'string'}, {'const': 'SQL_agent', 'type': 'string'}, {'const': 'DOCS_agent', 'type': 'string'}]}}, 'required': ['next'], 'type': 'object'}}}}}
                #  Messge : content='' additional_kwargs={'parsed': RouteResponse(next='FINISH'), 'refusal': None} response_metadata={'token_usage': None, 'model_name': '', 'system_fingerprint': 'fp_b705f0c291', 'prompt_filter_results': [{'prompt_index':
                # 0, 'content_filter_results': {'hate': {'filtered': False, 'severity': 'safe'}, 'self_harm': {'filtered': False, 'severity': 'safe'}, 'sexual': {'filtered': False, 'severity': 'safe'}, 'violence': {'filtered': False, 'severity':
                # 'safe'}}}]} id='run-d336cc90-664d-4ebd-a90d-d7deb371283d'
                #  Metadata : {'thread_id': '6194fedf-6088-4673-86a6-7085ba80d63d', 'langgraph_step': 3, 'langgraph_node': 'supervisor', 'langgraph_triggers': ['SQL_agent'], 'langgraph_path': ('__pregel_pull', 'supervisor'), 'langgraph_checkpoint_ns':
                # 'supervisor:19bea099-f575-621d-159e-0139641e616f', 'checkpoint_ns': 'supervisor:19bea099-f575-621d-159e-0139641e616f', 'ls_provider': 'azure', 'ls_model_name': 'gpt-4o-mini', 'ls_model_type': 'chat', 'ls_temperature': None,
                # 'structured_output_format': {'kwargs': {'method': 'json_schema'}, 'schema': {'type': 'function', 'function': {'name': 'RouteResponse', 'description': "Structured output for the supervisor's routing decision.", 'parameters': {'properties':
                # {'next': {'anyOf': [{'const': 'FINISH', 'type': 'string'}, {'const': 'SQL_agent', 'type': 'string'}, {'const': 'DOCS_agent', 'type': 'string'}]}}, 'required': ['next'], 'type': 'object'}}}}}

                # print(f"Message: {message.content}")
                # print(f"Metadata: {metadata}")
                if metadata["langgraph_node"] == "agent":
                    if message.content:
                        delta_message = {
                            "type": "agent_message_delta",
                            "delta": message.content,
                        }
                        yield f"data: {json.dumps(delta_message)}\n\n"

                # delta_message = {
                #     "type": "agent_message_delta",
                #     "delta": message.content,
                # }
                # yield f"data: {json.dumps(delta_message)}\n\n"

                # for node, updates in event.items():
                #     if node == "supervisor" and "next" in updates:
                #         next_agent = updates["next"]
                #         if next_agent != "FINISH":
                #             routing_message = {
                #                 "type": "routing_message",
                #                 "delta": f"Routing to {'database analysis' if next_agent == 'SQL_agent' else 'document retrieval'}.\n\n",
                #             }
                #             yield f"data: {json.dumps(routing_message)}\n\n"
                #     elif "messages" in updates:
                #         for msg in updates["messages"]:
                #             if isinstance(msg, AIMessage):
                #                 delta_message = {
                #                     "type": "agent_message_delta",
                #                     "delta": msg.content,
                #                 }
                #                 yield f"data: {json.dumps(delta_message)}\n\n"

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

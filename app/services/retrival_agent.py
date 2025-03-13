from langchain_core.tools import tool
from langchain_core.tools.base import BaseTool

from app.core.config import settings
from app.services.indexer import IndexerService
from app.services.memory import MemoryService
from app.services.react_agent import create_react_agent
from app.utils.logger import logger


class RetrievalAgent:
    """
    Agent specialized in document retrieval.
    Handles knowledge retrieval from vector stores.
    """

    def __init__(self, indexer: IndexerService):
        """
        Initialize Retrieval Agent with indexer and tools.

        Args:
            indexer (IndexerService): Service for document indexing and retrieval
        """
        self.llm = settings.local_llm
        self.indexer = indexer
        self.retrieval_tool = self._create_retrieval_tool()
        self.tools = [self.retrieval_tool]

    def _create_retrieval_tool(self) -> BaseTool:
        """
        Create a document retrieval tool that can fetch relevant documents
        from the vector store based on a query.

        Returns:
            BaseTool: The document retrieval tool
        """

        @tool
        async def retrieve_document(query: str) -> str:
            """
            Retrieve relevant documents from the vector store based on the query.

            Args:
                query (str): The search query to find relevant documents

            Returns:
                str: Concatenated content from relevant documents
            """
            logger.debug(f"Retrieving document for query: {query}")
            if not self.indexer.vector_store:
                raise ValueError("Vector store is not initialized")

            retriever = self.indexer.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5},
            )

            docs = await retriever.ainvoke(query)
            if not docs:
                logger.debug("No documents found for the query")
                return "No documents found."

            logger.debug(f"{len(docs)} documents retrieved.")
            context = "\n\n".join(
                [
                    f"Document {i + 1}: \n {doc.page_content}"
                    for i, doc in enumerate(docs)
                ]
            )
            return context

        return retrieve_document

    async def create_retrieval_agent(self, memory: MemoryService):
        """
        Create a ReAct agent specialized in document retrieval.

        Args:
            memory (MemoryService): Service for maintaining conversation context

        Returns:
            A ReAct agent configured for document retrieval
        """
        retrieval_prompt = """
You are a specialized document retrieval assistant. Your task is to find information from a knowledge base.
Use the retrieved content to answer the user's question. If the user's question is answered without information from the document, answer directly.

**FOLLOW THESE STEPS FOR EACH QUERY:**
    1. Analyze the query to identify key concepts and information needs.
    2. If the query is a general greeting (e.g., "hi", "hello", "how are you?"), respond directly without retrieving documents.
    3. Otherwise, use the `retrieve_document` tool with precise search terms.
    4. Present the most relevant information from retrieved documents.
    5. If information is not found, clearly state this limitation.

**IMPORTANT**:
- Base your responses ONLY on the retrieved documents when applicable. Do not invent or assume information.
- Clearly distinguish between direct information from documents and any necessary inferences.
- Respond to simple greetings or small talk directly without document retrieval.
"""

        agent_memory = None
        if memory:
            agent_memory = await memory.get_memory_saver()
        if not agent_memory:
            logger.error("Agent memory is not initialized")
            raise ValueError("Agent memory is not initialized.")

        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=retrieval_prompt,
            checkpointer=agent_memory,
        )

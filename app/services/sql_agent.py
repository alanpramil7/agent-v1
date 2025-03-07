from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase

from app.core.config import settings
from app.services.memory import MemoryService
from app.services.react_agent import create_react_agent
from app.utils.logger import logger


class SqlAgent:
    """
    Agent specialized in SQL database queries.
    Handles database queries using ReAct framework.
    """

    def __init__(self):
        """
        Initialize SQL Agent with database connection and tools.
        """
        self.llm = settings.llm
        self.db = SQLDatabase.from_uri(settings.database)
        self.sql_toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.sql_tools = self.sql_toolkit.get_tools()

    async def create_sql_agent(self, memory: MemoryService):
        """
        Create a ReAct agent specialized in SQL queries.

        Args:
            memory (MemoryService): Service for maintaining conversation context

        Returns:
            A ReAct agent configured for SQL operations
        """
        sql_prompt = """
        You are a specialized SQL database agent. Your task is to help users retrieve
        and analyze data from SQL databases.

        FOLLOW THESE STEPS SEQUENTIALLY FOR EACH QUERY:
        1. First, use `sql_db_list_tables` to identify available tables
        2. Then, use `sql_db_schema` on the most relevant tables to understand their structure
        3. Develop an SQL query based on the user's question:
           - Use double quotes around column names: `"column_name"`
           - ALWAYS include a LIMIT clause (preferably LIMIT 10)
           - Use exact column names from the schema
           - Be selective in columns - avoid `SELECT *` unless needed
           - Apply appropriate WHERE clauses and aggregations
           - NEVER use modification statements (INSERT, UPDATE, DELETE, DROP)
        4. Execute the query with `sql_db_query`
        5. Explain the results in a clear, concise manner

        IMPORTANT: If errors occur, diagnose the issue and try alternative approaches.
        Present final results in a well-formatted, easy-to-understand manner.
        """

        agent_memory = None
        if memory:
            agent_memory = await memory.get_memory_saver()
        if not agent_memory:
            logger.error("Agent memory is not initialized")
            raise ValueError("Agent memory is not initialized.")

        return create_react_agent(
            model=self.llm,
            tools=self.sql_tools,  # Fixed: was self.SqlAgent
            prompt=sql_prompt,
            checkpointer=agent_memory,
        )

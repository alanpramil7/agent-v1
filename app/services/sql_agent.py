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
            You are a FinOps SQL database agent specializing in cloud cost analysis, optimization, and insights.
            Your primary task is to help users retrieve, analyze, and optimize cloud cost and usage data efficiently.

            FOLLOW THESE STEPS SEQUENTIALLY FOR EACH QUERY:
            Identify Available Tables:

            Use sql_db_list_tables to fetch the list of tables.
            Understand Table Structures:

            Use sql_db_schema to inspect relevant tables and retrieve precise column names.
            Construct an Optimized SQL Query:

            Use double quotes around column names: "column_name".
            ALWAYS include a LIMIT clause (LIMIT 10 unless otherwise specified).
            Select only necessary columns to reduce query load and improve efficiency.
            Use WHERE clauses to filter data by time range, cost category, service, or resource type.
            Apply aggregations (e.g., SUM, AVG, MAX, MIN, GROUP BY) for cost trends and optimization insights.
            NEVER use modification statements (INSERT, UPDATE, DELETE, DROP).
            Execute the Query:

            Run the query using sql_db_query.
            Analyze and Explain Results Clearly:

            Summarize cost trends, anomalies, or optimizations based on the query output.
            While using cost always go for the blended cost columnustments.
            ADDITIONAL RULES:
            Error Handling: If an error occurs, diagnose the issue and try an alternative approach.
            Performance Considerations: Optimize queries for performance by reducing data scan size and using indexes where applicable.
            Cloud Context Awareness: Provide contextual recommendations based on FinOps principles, such as cost efficiency, resource allocation, and forecasting.
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

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
            You are a FinOps SQL Database Agent specializing in cloud cost analysis, optimization, and actionable financial insights. 
            Your mission is to help users retrieve, analyze, and optimize cloud cost and usage data while identifying cost-saving opportunities and ensuring adherence to FinOps best practices.

            Follow these steps for each query:

            1. Identify Available Tables:
               - Use the sql_db_list_tables function to fetch a list of available tables in the database.

            2. Understand Table Structures:
               - Use the sql_db_schema function to inspect table schemas and retrieve precise column names. This ensures accurate query construction.

            3. Construct an Optimized SQL Query:
               - Always enclose column names in double quotes (e.g., "column_name") to avoid conflicts with reserved keywords.
               - Include a LIMIT clause (default: LIMIT 10) unless the user specifies otherwise, to control data retrieval and enhance performance.
               - Select only the necessary columns to minimize query load.
               - Use WHERE clauses to filter data by criteria such as time range, cost category, service, resource type, or cost allocation tags.
               - Apply aggregations (e.g., SUM, AVG, MAX, MIN, GROUP BY) to derive cost and usage trends.
               - Use the "blended_cost" column as the standard metric to ensure consistency in cost calculations.
               - Integrate FinOps-specific analysis by:
                    Detecting cost anomalies and overspending trends.
                    Evaluating reserved instance coverage and savings plan opportunities.
                    Identifying opportunities for instance right-sizing and cost efficiency.
                    Comparing actual usage against forecasted trends.
                    Highlighting underutilized or unutilized resources.

            4. Execute the Query:
               - Use the sql_db_query function to run the constructed query and retrieve the results.

            5. Analyze and Explain Results Clearly:
               - When giving recommendations consider getting data from multiple relevant tables for calculations and provide accurate recommendations.
               - Summarize cost and usage trends, pinpoint anomalies, and provide actionable optimization recommendations.
               - Offer contextual FinOps insights, such as:
                    Strategies for improving cost allocation and tagging.
                    Recommendations for switching to more cost-effective pricing models (e.g., reserved instances, savings plans).
                    Forecasting future costs based on historical trends.
               - Ensure your explanations are clear, concise, and directly aligned with FinOps principles.

            Additional Guidelines:
            - Error Handling:
                If an error occurs (e.g., syntax error, incorrect table/column names), diagnose the issue and suggest an alternative query approach.

            - Performance Considerations:
                Optimize queries to reduce data scan size by leveraging appropriate filters and indexes.

            - Cloud and Financial Context Awareness:
                Always align your analysis with FinOps best practices, focusing on cost efficiency, optimal resource allocation, and proactive forecasting.
                Consider industry standards for improving cloud cost management and operational efficiency.

            Your responses should always strive for clarity and provide actionable recommendations that empower users to achieve better cloud cost management and efficiency.
        """

        agent_memory = None
        if memory:
            agent_memory = await memory.get_memory_saver()
        if not agent_memory:
            logger.error("Agent memory is not initialized")
            raise ValueError("Agent memory is not initialized.")

        return create_react_agent(
            model=self.llm,
            tools=self.sql_tools,
            prompt=sql_prompt,
            checkpointer=agent_memory,
        )

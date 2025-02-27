# SQL Data Chat Agent User Guide

## Introduction

The SQL Data Chat Agent provides a conversational interface to your SQL database, allowing you to ask questions in natural language and receive accurate answers based on your data. This guide will help you understand how to effectively use the agent.

### Purpose and Benefits

The SQL Data Chat Agent serves as a bridge between technical database systems and business users who need data insights without writing SQL. Key benefits include:

- **No SQL Knowledge Required**: Ask questions in plain English instead of writing complex queries
- **Faster Insights**: Get answers in seconds rather than waiting for data team availability
- **Data Democratization**: Enable all team members to access data-driven insights directly
- **Reduced Technical Burden**: Free up data teams from routine query requests
- **Business Context**: Receive answers with relevant business context and explanations

### Target Users

This agent is designed for various user profiles:

- **Business Analysts**: Who need regular access to data but may lack SQL expertise
- **Department Managers**: Who require data-driven insights for decision making
- **Finance Teams**: For quick access to cost and resource utilization data
- **Operations Staff**: For monitoring and troubleshooting Azure resources
- **Executives**: For high-level insights without technical details

## Getting Started

### Accessing the Agent

The agent is accessible through an API. Depending on your organization's setup, you might interact with it through:

1. **Web Interface**: A custom web application that provides a chat-like experience
2. **Direct API Calls**: For integration with existing tools and applications
3. **Integration with Other Applications**: Built into dashboards, internal portals, or tools

#### Web Interface Access

If a web interface is available:

1. Navigate to the URL provided by your administrator (typically `http://[server-address]:8000/`)
2. Log in using your organizational credentials (if authentication is enabled)
3. Use the chat interface to enter your questions
4. View responses in the conversation thread

#### API Access

For direct API interaction:

1. Obtain necessary API access credentials (if applicable)
2. Use the endpoints documented in the API documentation
3. Format questions according to the API specifications

### Basic Interaction

The core interaction with the agent involves:

1. Asking a question in natural language
2. Receiving a response that includes relevant data from your SQL database

#### Sample Interaction

**User**: "What was our total Azure spending last month?"

**Agent**: "Based on the database query, your total Azure spending for February 2024 was $45,678.90. This represents a 5% increase compared to January 2024. The largest contributors to this spend were Virtual Machines ($15,243.50), Storage ($10,876.30), and Azure SQL ($8,954.20)."

#### First-Time Experience

When using the agent for the first time:

1. Start with simple, direct questions to understand how the agent responds
2. Experiment with different question phrasing to find what works best
3. Ask the agent to explain its sources or reasoning when needed
4. Build complexity gradually as you become familiar with the system

## Asking Effective Questions

### Question Types

The agent can handle various types of questions:

1. **Factual Queries**: Questions asking for specific facts or figures
   - "What was our total Azure spending last month?"
   - "How many virtual machines are running in our production environment?"
   - "What is the average cost per GB of our storage accounts?"
   - "How many resources do we have in the East US region?"
   - "What percentage of our budget was spent on networking services?"

2. **Comparative Queries**: Questions asking to compare data
   - "How does our current Azure spending compare to the previous quarter?"
   - "Which resource group has the highest spending this month?"
   - "Compare the cost efficiency of our development vs. production environments."
   - "What's the cost difference between our SQL databases and Cosmos DB instances?"
   - "Show me cost trends across all regions over the past six months."

3. **Trend Queries**: Questions asking about changes over time
   - "Show me the trend of our Azure storage costs over the past year."
   - "How has our VM usage changed since last quarter?"
   - "What's the month-over-month growth rate of our database spending?"
   - "Has our networking cost been increasing or decreasing this year?"
   - "Plot our container service usage over time."

4. **Exploratory Queries**: Open-ended questions about data
   - "What insights can you provide about our cloud spending patterns?"
   - "Where are we seeing unusual resource consumption?"
   - "What opportunities exist for cost optimization in our environment?"
   - "Are there any underutilized resources we should consider scaling down?"
   - "What are the key cost drivers in our Azure environment?"

5. **Resource-Specific Queries**: Questions about particular Azure resources
   - "List all our storage accounts with more than 1TB of data."
   - "Which of our VMs have the lowest utilization rates?"
   - "What are the specifications and costs of our premium SQL databases?"
   - "Show me all resources with 'prod' in their name or tags."
   - "Which App Service Plans are hosting multiple applications?"

### Query Best Practices

To get the most accurate and helpful responses:

1. **Be Specific**: Clearly state what information you're looking for
   - Good: "What was our Azure VM spending in the East US region last month?"
   - Less effective: "Tell me about our Azure spending."
   
   **Why it matters**: Specific queries help the agent understand exactly what data to retrieve and how to format the response. This reduces ambiguity and ensures you get precisely the information you need.

2. **Specify Time Periods**: Include relevant time frames in your questions
   - Good: "What resources had the highest costs in Q1 2023?"
   - Less effective: "What resources are expensive?"
   
   **Why it matters**: Time constraints are critical for financial and usage data. Without them, the agent might default to recent data or need to ask follow-up questions to clarify your intent.

3. **Use Business Terms**: You can use familiar business terminology rather than database-specific terms
   - Good: "Which departments exceeded their cloud budget last quarter?"
   - No need for: "SELECT department, sum(cost) FROM expenses WHERE..."
   
   **Why it matters**: The agent is designed to understand business language and translate it to technical queries. Using familiar terms makes your questions more natural and often leads to better responses.

4. **Ask Follow-up Questions**: You can refer to previous questions for context
   - "Which resource group had the highest spending?"
   - Then: "What specific services drove those costs?"
   
   **Why it matters**: The agent maintains conversation context, allowing you to drill down into details without repeating all the original parameters. This creates a more natural dialogue flow.

5. **Limit the Scope When Possible**: Narrow your question to relevant subsets of data
   - Good: "Show me storage costs for our production workloads."
   - Less effective: "Show me all our costs."
   
   **Why it matters**: More focused questions typically result in more precise answers and better performance, especially with large datasets.

6. **Use Consistent Terminology**: Try to use the same terms consistently across your questions
   - For example, consistently use either "resource group" or "resource groups" rather than switching between different terms
   
   **Why it matters**: While the agent can handle variations, consistency helps it better understand your intent and maintain context throughout the conversation.

7. **Request Specific Formats When Needed**: You can ask for data in particular formats
   - "Show the top 5 expensive resources in a table format."
   - "Provide cost breakdown in percentages."
   
   **Why it matters**: The agent can tailor its response format to your needs, making the information easier to understand or use for specific purposes.

### Formulating Complex Questions

For advanced insights, you can formulate more complex questions that combine multiple aspects:

1. **Multi-dimensional Analysis**:
   - "Show me our VM costs broken down by region, size, and operating system for the last quarter."
   - "Compare our storage costs across departments, adjusting for data volume."

2. **Conditional Queries**:
   - "Which resources have increased in cost by more than 20% compared to last month?"
   - "List all storage accounts with less than 10% utilization but more than $100 in monthly costs."

3. **Insight-Oriented Questions**:
   - "Identify potential cost-saving opportunities in our Azure environment based on resource utilization."
   - "What patterns exist in our spending across different project tags?"

4. **Time-Series Analysis**:
   - "Show our peak usage periods for compute resources over the past three months."
   - "Forecast our storage cost growth based on the trends from the last year."

## Understanding Responses

### Response Components

Typical responses from the agent include:

1. **Direct Answer**: A clear response to your question
   - Example: "Your total Azure spending last month was $45,678.90."

2. **Data Summary**: Key figures or statistics from the database
   - Example: "The breakdown shows $15,243.50 for VMs, $10,876.30 for Storage, and $8,954.20 for Azure SQL."

3. **Context**: Additional information to help understand the data
   - Example: "This represents a 5% increase compared to the previous month."

4. **Source Information**: Details about which data was used to generate the answer
   - Example: "This information is based on the Azure cost records from February 1-29, 2024."

5. **Potential Actions**: Suggestions for related inquiries or next steps
   - Example: "You might want to examine the VM cost increase in the East US region, which accounts for most of the overall increase."

### Interpreting the Results

To get the most value from responses:

1. **Check the Time Period**: Verify the response is for the time period you intended
2. **Note Any Assumptions**: Be aware of any assumptions the agent made to answer your question
3. **Consider Completeness**: For very broad questions, the agent might focus on the most significant data points
4. **Look for Insights**: Beyond raw numbers, look for patterns or anomalies the agent highlights
5. **Verify Against Expectations**: If a result seems unexpected, ask for clarification or validation

### Data Visualization

The agent provides text-based responses. If you need visualizations:

1. Export the data mentioned in the response
2. Use business intelligence tools for visualization
3. Consider asking for specific formats ("Can you format this as a table?")

#### Text-Based Visualization Options

The agent can provide basic text-based visualizations:

```
Monthly Cost Trend (in $1000s):
Jan: ■■■■■■■■■■ ($42.1)
Feb: ■■■■■■■■■■■ ($45.7)
Mar: ■■■■■■■■■■■■ ($48.3)
Apr: ■■■■■■■■■■■■■ ($51.9)
```

Or formatted tables:

```
| Service Type | Cost      | % of Total |
|--------------|-----------|------------|
| Virtual Machines | $15,243.50 | 33.4% |
| Storage     | $10,876.30 | 23.8% |
| Azure SQL   | $8,954.20  | 19.6% |
| Networking  | $5,671.40  | 12.4% |
| Other       | $4,933.50  | 10.8% |
```

## Advanced Usage

### Complex Queries

The agent can handle complex analytical questions that would require multiple SQL queries:

- "Which Azure services show the highest month-over-month growth in both usage and cost?"
- "Identify resources that are underutilized but generating significant costs."
- "Compare our cost efficiency metrics across different environment types and regions."
- "What percentage of our Azure spending is on resources tagged as 'temporary' or 'development'?"
- "Find correlations between resource uptime and cost across our subscription."

### Conversation Strategies

To conduct effective analytical sessions:

1. **Start Broad, Then Narrow**: Begin with an overview question, then drill down into specifics
   - First: "What were our highest cloud expenses last quarter?"
   - Then: "Break down the compute costs by resource group."
   - Finally: "Which specific VMs in that resource group are driving the highest costs?"

2. **Compare Multiple Dimensions**: Build understanding by comparing across different facets
   - "How do our storage costs compare across regions?"
   - "Now compare those same costs across different departments."
   - "Which combination of region and department has the highest cost per GB?"

3. **Explore Anomalies**: When you spot something unusual, investigate further
   - "Why did we see a spike in network costs in March?"
   - "Was this spike consistent across all regions?"
   - "Which specific resources contributed most to this increase?"

4. **Test Hypotheses**: Use the agent to validate or disprove assumptions
   - "I suspect our development environments are oversized. Can you compare utilization rates between production and development VMs?"

### Handling Limitations

The agent has some limitations:

1. **Data Freshness**: The agent can only access data that exists in the database
   - **Solution**: Ask about the recency of data if it's critical for your question
   - **Example**: "When was the cost data last updated in the system?"

2. **Query Complexity**: Extremely complex queries might be simplified
   - **Solution**: Break down complex questions into a series of simpler ones
   - **Example**: Instead of one complex query with many conditions, ask several focused questions

3. **Domain Knowledge**: The agent has knowledge about Azure and cloud concepts but may have limitations with organization-specific terminology
   - **Solution**: Provide context for organization-specific terms or acronyms
   - **Example**: "In our company, 'Project Horizon' refers to our main e-commerce platform. What were the Azure costs for Project Horizon last month?"

If you encounter a limitation, try:
- Breaking down complex questions into simpler ones
- Providing more context in your question
- Using more standard terminology

### Exporting and Using Data

While the agent provides insights directly, you might want to use the data elsewhere:

1. **Copy and Paste**: For simple data points, copy from the conversation
2. **Request Formatted Output**: Ask for data in formats easy to copy (CSV, JSON)
   - Example: "Can you give me this data in CSV format?"
3. **API Integration**: For regular reporting, work with developers to integrate the API with your tools
4. **Follow-up for Further Analysis**: Use the insights to guide deeper analysis in specialized tools

## Troubleshooting

### Common Issues

1. **Unclear Responses**: If the response seems vague or incorrect
   - Rephrase your question to be more specific
   - Check if the time period is clearly specified
   - Ask for clarification ("Can you explain how you calculated that?")
   - Request the SQL query that was generated ("Can you show me the query you used?")
   - Try alternative wording for key concepts

2. **Missing Data**: If the agent indicates data is missing
   - Verify the data exists in the database
   - Check if you're using the correct terminology
   - Consider if the data might be in a different format or location
   - Ask about available data ("What time periods do you have data for?")
   - Confirm table or field names ("What fields are available for VM costs?")

3. **Performance Issues**: If responses are slow
   - Simplify your question
   - Consider breaking it into multiple smaller questions
   - Ask for specific data rather than broad analyses
   - Specify a narrower time range if applicable
   - Limit the scope to fewer resources or regions

4. **Context Confusion**: If the agent misunderstands the context
   - Start a new conversation if the context has become too complex
   - Explicitly state all parameters rather than relying on previous context
   - Use more precise terminology in your questions
   - Correct misunderstandings directly ("No, I meant East US region, not West US")

### Example Troubleshooting Scenarios

**Scenario 1: Ambiguous Time Period**

User: "What's our Azure spending?"
Agent: "For which time period would you like to know the Azure spending?"
User: "For Q1 this year."
Agent: [Provides answer for Q1]

**Scenario 2: Terminology Clarification**

User: "Show me the costs for our Horizon project."
Agent: "I don't see any resources or tags specifically labeled 'Horizon' in the database. Could you clarify what you mean by the Horizon project? It might be labeled differently in the data."
User: "Horizon is our internal name. Look for resources tagged with project='ecommerce-platform'."
Agent: [Provides answer based on the clarified information]

**Scenario 3: Complex Query Simplification**

User: "Compare the cost-efficiency of all our VMs across regions, operating systems, and instance types, accounting for utilization rates and identifying optimization opportunities."
Agent: "That's a complex analysis. Let me break it down:
1. First, here's the average cost per VM by region...
2. Now, for utilization rates across operating systems...
3. For instance types, here are the efficiency metrics...
Would you like me to focus on any particular aspect for optimization recommendations?"

### Getting Help

If you continue to experience issues:

1. Check the logs for error messages
2. Contact your system administrator
3. Refer to the developer documentation for more technical details
4. Ask the agent for help with its capabilities ("What types of questions can you answer?")
5. Request examples of well-formed questions ("Can you give me examples of questions about Azure costs?")

## Best Practices and Tips

### Organizational Usage Patterns

For team or organization-wide use:

1. **Establish Common Terminology**: Agree on standard terms for resources, projects, and metrics
2. **Share Effective Questions**: Document questions that provide particularly useful insights
3. **Create Question Templates**: Develop templates for routine analyses that team members can adapt
4. **Define Usage Guidelines**: Establish when to use the agent versus other analytical tools
5. **Collect Feedback**: Regularly gather user experiences to improve prompts and identify gaps

### Power User Tips

Advanced techniques for getting the most value:

1. **Chained Analysis**: Use insights from one question to inform follow-up questions
2. **Comparative Time Periods**: Always compare current data to appropriate historical periods
3. **Contextual Awareness**: Include business events or changes when interpreting trends
4. **Scheduled Questions**: Set up regular queries for consistent tracking of key metrics
5. **Question Refinement**: Iteratively improve your question phrasing based on response quality
6. **Metadata Exploration**: Ask about available data dimensions before deep analysis
7. **Anomaly Validation**: Always verify surprising findings with follow-up questions

### Security and Compliance Considerations

When working with sensitive data:

1. **Data Sharing**: Don't share responses containing sensitive information outside authorized channels
2. **Authentication**: Always use your own credentials and don't share access
3. **Query Auditing**: Be aware that queries may be logged for compliance purposes
4. **PII Awareness**: Avoid requesting personally identifiable information unless necessary and authorized
5. **Confidential Projects**: Use established project codes rather than descriptive names for sensitive initiatives 
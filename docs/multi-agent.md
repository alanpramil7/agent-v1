# Mutli Agent Archicture

    A Multi Agent has many small agents configured to it, and it can use any agent at any time based on the user question

## Orchestrator Agent

- Its responsibility is to route the user question to correct agent (SQL Agent / Retrival Agent)
- If the user question is about Amadis and Cloudadi it should route to Retrival Agent.
- If the user question is about the resource details and databse related it should route to sql agent.

## SQL Agent

- This uses azure openai(gpt-4o-mini) to generate responses. Tried with local llm but it cant corectly generate sql queries and tool calling/function calling is not supported in all local models
- Has three tools 
    - `sql_db_list_tables`: Used to list all the sql tables in the database.
    - `sql_db_schema`: Use to get the schema of a table, takes table name as input.
    - `sql_db_query`: Used to execute the generated sql queries and get answer, takes sql query as input.

- User Question -> List all tables -> Get schema for tables related to user question -> Genrate Query -> Execute Query -> Answer user question.

## Retrival Agent

- This uses local llm to call the retrival tool and then retrive document and using the document as context and answer the user quesion.
- `retrieve_document`: Use this tool to retrive documents that answer the user query. Input to this tool is the query that needs to be searched.

- User Question -> call retriver tool -> retriver docs based on query -> Answer user question.



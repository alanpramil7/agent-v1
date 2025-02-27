# SQL Data Chat Agent API Documentation

## API Overview

The SQL Data Chat Agent exposes a RESTful API for interacting with the system. The API is built using FastAPI and provides endpoints for querying the agent and checking the health of the service.

### API Design Principles

The API is designed following these principles:

- **Simplicity**: Minimal endpoint design focused on core functionality
- **Consistency**: Uniform request/response patterns across endpoints
- **Robustness**: Comprehensive error handling and validation
- **Performance**: Optimized for handling concurrent requests
- **Extensibility**: Structured to allow adding new endpoints without breaking changes

### API Versioning

The API uses path-based versioning with the `/v1` prefix. This approach allows:

- Forward compatibility as the API evolves
- Clear indication of the API contract version
- Support for multiple API versions simultaneously if needed
- Seamless transition when breaking changes are required

## Base URL

```
http://{host}:{port}/v1
```

By default, the service runs on `0.0.0.0:8000`.

### Environment Configuration

The host and port can be configured using environment variables:

```
HOST=0.0.0.0
PORT=8000
```

For production deployments, it's recommended to use a reverse proxy (like Nginx or Traefik) in front of the application.

## Endpoints

### Process Question

Processes a natural language question and returns a complete response.

#### Request Details

- **URL**: `/agent`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Description**: Processes a natural language question about SQL data and returns a complete answer based on database information and available knowledge.

#### Request Body Schema

```json
{
  "question": "string",
  "thread_id": "string (optional)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | string | Yes | The natural language question to process |
| `thread_id` | string | No | Optional thread identifier for maintaining conversation context across multiple requests |

#### Response Format

```json
"string"
```

The response is a string containing the agent's answer to the question.

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Successful response with agent's answer |
| 400 | Bad request (invalid payload format) |
| 422 | Validation error (missing required fields) |
| 500 | Internal server error |

#### Example Request

```bash
curl -X POST "http://localhost:8000/v1/agent" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What was our total Azure spending last month?",
       "thread_id": "user123-session456"
     }'
```

#### Example Response

```json
"Based on the SQL database, your total Azure spending last month was $42,651.23. This represents a 12% increase compared to the previous month, primarily due to increased usage of Azure Virtual Machines and Azure Storage services."
```

#### Error Response Example

```json
{
  "detail": "Error processing user request: Failed to connect to database"
}
```

### Stream Question

Processes a natural language question and streams the response as it's being generated.

#### Request Details

- **URL**: `/agent/stream`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Description**: Processes a natural language question about SQL data and streams the response in real-time as it's being generated.

#### Request Body Schema

```json
{
  "question": "string",
  "thread_id": "string (optional)"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `question` | string | Yes | The natural language question to process |
| `thread_id` | string | No | Optional thread identifier for maintaining conversation context across multiple requests |

#### Response Format

A streaming response with `text/plain` content type, delivering chunks of the answer as they are generated.

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Successful streaming response |
| 400 | Bad request (invalid payload format) |
| 422 | Validation error (missing required fields) |
| 500 | Internal server error |

#### Example Request

```bash
curl -X POST "http://localhost:8000/v1/agent/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "What was our total Azure spending last month?",
       "thread_id": "user123-session456"
     }'
```

### Process Document

Uploads and processes a document file, adding its content to the vector store for retrieval during queries.

#### Request Details

- **URL**: `/document`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Description**: Uploads a document file (PDF, DOCX, etc.), processes its content, and adds it to the vector store for later retrieval.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | The document file to process and index |

#### Response Format

```json
{
  "status": "string",
  "file_name": "string",
  "chunks": "integer"
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Successful document processing |
| 400 | Bad request (missing file) |
| 500 | Internal server error |

#### Example Request

```bash
curl -X POST "http://localhost:8000/v1/document" \
     -F "file=@/path/to/document.pdf"
```

#### Example Response

```json
{
  "status": "Successfully indexed file",
  "file_name": "document.pdf",
  "chunks": 24
}
```

### Process Website

Processes and indexes content from a website URL, adding it to the vector store for retrieval during queries.

#### Request Details

- **URL**: `/website`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Description**: Crawls a website URL, processes its content, and adds it to the vector store for later retrieval.

#### Request Body Schema

```json
{
  "url": "string"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | The URL of the website to crawl and index |

#### Response Format

```json
{
  "status": "string",
  "url": "string",
  "chunks": "integer"
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Successful website processing |
| 422 | Validation error (invalid URL) |
| 500 | Internal server error |

#### Example Request

```bash
curl -X POST "http://localhost:8000/v1/website" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://example.com/documentation"
     }'
```

#### Example Response

```json
{
  "status": "Successfully indexed website",
  "url": "https://example.com/documentation",
  "chunks": 36
}
```

### Process Wiki

Processes and indexes content from a wiki, adding it to the vector store for retrieval during queries.

#### Request Details

- **URL**: `/wiki`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Description**: Retrieves wiki content from a specified source (e.g., Azure DevOps), processes it, and adds it to the vector store for later retrieval.

#### Request Body Schema

```json
{
  "organization": "string",
  "project": "string",
  "wikiIdentifier": "string"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organization` | string | Yes | The organization that contains the wiki |
| `project` | string | Yes | The project that contains the wiki |
| `wikiIdentifier` | string | Yes | The identifier of the wiki to process |

#### Response Format

```json
{
  "status": "string",
  "wiki": "string",
  "chunks": "integer"
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Successful wiki processing |
| 422 | Validation error (missing required fields) |
| 500 | Internal server error (including missing access token) |

#### Example Request

```bash
curl -X POST "http://localhost:8000/v1/wiki" \
     -H "Content-Type: application/json" \
     -d '{
       "organization": "MyOrg",
       "project": "MyProject",
       "wikiIdentifier": "ProjectWiki"
     }'
```

#### Example Response

```json
{
  "status": "Successfully indexed wiki",
  "wiki": "ProjectWiki",
  "chunks": 52
}
```

### Health Check

Checks the health status of the service.

#### Request Details

- **URL**: `/check-health`
- **Method**: `GET`
- **Description**: Returns basic health and version information about the service. Useful for monitoring and deployment verification.

#### Response Format

```json
{
  "status": "string",
  "version": "string"
}
```

#### Parameters

This endpoint takes no parameters.

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Service is healthy |
| 500 | Service is unhealthy |

#### Example Request

```bash
curl -X GET "http://localhost:8000/check-health"
```

#### Example Response

```json
{
  "status": "Healthy",
  "version": "0.1"
}
```

## Request Models

### AgentProcessingRequest

```python
class AgentProcessingRequest:
    question: str  # The natural language question to process
    thread_id: Optional[str] = None  # Optional thread identifier for conversation context
```

This Pydantic model validates incoming requests to ensure they contain the required fields and proper data types.

### Database Schema Understanding

The API doesn't require direct knowledge of the database schema. The agent dynamically explores the database structure for each question, making it resilient to schema changes.

## Error Responses

The API returns standard HTTP status codes to indicate the success or failure of a request.

### Status Codes

- **200 OK**: The request was successful
- **400 Bad Request**: The request was malformed
- **422 Unprocessable Entity**: The request contained invalid parameters
- **500 Internal Server Error**: An error occurred while processing the request

### Error Response Format

Error responses include a detail message that provides more information about the error.

```json
{
  "detail": "Error processing user request: [error message]"
}
```

### Common Error Scenarios

1. **Database Connection Errors**
   ```json
   {
     "detail": "Error processing user request: Failed to connect to database"
   }
   ```

2. **Query Execution Errors**
   ```json
   {
     "detail": "Error processing user request: Error executing SQL query: syntax error in SQL statement"
   }
   ```

3. **Language Model Errors**
   ```json
   {
     "detail": "Error processing user request: Failed to generate response from language model"
   }
   ```

4. **Request Validation Errors**
   ```json
   {
     "detail": [
       {
         "loc": ["body", "question"],
         "msg": "field required",
         "type": "value_error.missing"
       }
     ]
   }
   ```

## Rate Limiting

The API does not currently implement rate limiting, but it's recommended to limit the number of requests to avoid overloading the service.

### Rate Limiting Recommendations

For production deployments, consider implementing rate limiting at the application level or using a reverse proxy:

- **Simple Applications**: Limit to 10 requests per minute per user
- **Enterprise Deployments**: Adjust limits based on expected usage patterns
- **Streaming Endpoints**: Consider connection duration limits in addition to request counts

### Future Rate Limiting Implementation

Future versions may implement rate limiting with the following features:
- Token bucket algorithm for request throttling
- User or API key-based quotas
- Graceful degradation during high load periods
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)

## Authentication

The API does not currently implement authentication. If deploying in a production environment, it's recommended to implement an authentication mechanism such as API keys or OAuth.

### Authentication Recommendations

For production deployments, consider implementing one of the following authentication methods:

1. **API Key Authentication**
   - Include API key in request header: `X-API-Key: your-api-key`
   - Implement key generation and management system
   - Enforce secure transmission via HTTPS

2. **OAuth 2.0**
   - Implement standard OAuth 2.0 flow
   - Support service-to-service authentication
   - Enable user-based access control

3. **JWT Tokens**
   - Issue JSON Web Tokens for authenticated sessions
   - Include claims for user identification and authorization
   - Implement token refresh mechanisms

### Security Best Practices

1. Always deploy the API with HTTPS in production
2. Store sensitive configuration (API keys, credentials) in environment variables
3. Implement proper request logging for security auditing
4. Consider implementing IP allowlisting for restrictive environments 
# SQL Data Chat Agent Installation Guide

## Prerequisites

Before installing the SQL Data Chat Agent, ensure you have the following prerequisites:

- Python 3.9 or higher
- Access to an Azure OpenAI service
- Access to a SQL database
- Git (for cloning the repository)

### Detailed Prerequisites

#### Python Environment

The application requires Python 3.9+ with pip. Check your Python version:

```bash
python --version
```

It's recommended to use a dedicated Python version manager like pyenv:

```bash
# Install pyenv (Linux/macOS)
curl https://pyenv.run | bash

# Install specific Python version
pyenv install 3.9.10
pyenv local 3.9.10
```

#### Azure OpenAI Requirements

You need an active Azure OpenAI resource with:

1. **GPT Model**: Deploy a GPT model (at least gpt-35-turbo or higher recommended)
2. **Embedding Model**: Deploy text-embedding-3-small model
3. **API Keys**: Generate API keys with appropriate permission level
4. **Resource Quota**: Ensure sufficient quota for your expected usage
5. **API Version**: Check compatibility with API version 2023-05-15 or newer

#### SQL Database Requirements

The system supports various SQL databases:

1. **SQLite**: Simplest setup for development, included in Python
2. **PostgreSQL**: Recommended for production (requires v10+)
3. **MySQL/MariaDB**: Also supported (requires v5.7+/v10.3+)
4. **Microsoft SQL Server**: Supported via pymssql or pyodbc
5. **Oracle**: Supported via cx_Oracle

For PostgreSQL, MySQL, SQL Server, or Oracle, ensure:
- A user account with SELECT permission on relevant tables
- Network connectivity from the application server
- Required client libraries are installed

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd agent-v1
```

For a specific version or branch:

```bash
git clone -b <branch-name> <repository-url>
```

### 2. Create a Virtual Environment

```bash
# Using venv
python -m venv .venv

# Activate the virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

Alternative using Conda:

```bash
# Create a Conda environment
conda create -n sql-agent python=3.9
conda activate sql-agent
```

### 3. Install Dependencies

```bash
# Install using pip
pip install -r requirements.txt
```

For development environments:

```bash
# Install with development dependencies
pip install -r requirements-dev.txt
```

For specific database backends, install additional dependencies:

```bash
# PostgreSQL
pip install psycopg2-binary

# MySQL
pip install mysqlclient

# SQL Server
pip install pymssql

# Oracle
pip install cx_Oracle
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the root directory of the project based on the provided `.env.example` file:

```bash
cp .env.example .env
```

Edit the `.env` file and set the following variables:

```
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_API_KEY=your-api-key

# Azure Embedding Configuration
AZURE_EMBEDDING_ENDPOINT=https://your-embedding-resource.openai.azure.com/
EMBEDDING_API_VERSION=2023-05-15

# Database Configuration
DATABASE=sqlite:///data/database.db
# Or for other databases:
# DATABASE=postgresql://username:password@host:port/dbname
# DATABASE=mysql://username:password@host:port/dbname

# Wiki Access Token (if needed)
WIKI_ACCESS_TOKEN=your-wiki-access-token

# Embedding Model
EMBEDDING_MODEL=text-embedding-3-small  # Embedding model to use
```

#### Advanced Configuration Options

Additional environment variables can be set for fine-tuning:

```
# Application Configuration
APP_NAME="AmBlue"  # Name of the application
APP_VERSION="0.1"  # Application version
APP_DESCRIPTION="Amadis AI Agent"  # Description shown in docs

# Server Configuration
HOST=0.0.0.0  # Bind address for the server
PORT=8000  # Port for the server
LOG_LEVEL=DEBUG  # Log level (DEBUG, INFO, WARNING, ERROR)

# Performance Tuning
MAX_CONNECTIONS=20  # Maximum database connections
TIMEOUT=30  # Query timeout in seconds
```

### 2. Data Directory Setup

The application uses a `data` directory to store documents and vector store data:

```bash
mkdir -p data/docs
mkdir -p data/vector_store
```

You can customize the data directory location by setting the `DATA_DIR` environment variable:

```
DATA_DIR=/path/to/custom/data
```

#### Document Storage

To preload documents for retrieval:

1. Create subdirectories for document types:
   ```bash
   mkdir -p data/documents/pdf
   mkdir -p data/documents/docx
   ```

2. Copy your documents to these directories:
   ```bash
   cp your-documents/*.pdf data/documents/pdf/
   cp your-documents/*.docx data/documents/docx/
   ```

### 3. Database Setup

Ensure your database is properly set up and accessible with the connection string provided in the `.env` file. The application requires read access to the database but does not modify any data.

#### SQLite Setup

For SQLite (simplest option):

```bash
# No additional setup needed, just ensure the path exists
mkdir -p data
touch data/database.db
```

#### PostgreSQL Setup

```bash
# Create database and user
psql -U postgres -c "CREATE DATABASE azure_data;"
psql -U postgres -c "CREATE USER azure_reader WITH PASSWORD 'securepassword';"
psql -U postgres -c "GRANT CONNECT ON DATABASE azure_data TO azure_reader;"
psql -U postgres -d azure_data -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO azure_reader;"
psql -U postgres -d azure_data -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO azure_reader;"
```

Then update your `.env` file:
```
DATABASE=postgresql://azure_reader:securepassword@localhost:5432/azure_data
```

#### MySQL Setup

```bash
# Create database and user
mysql -u root -p -e "CREATE DATABASE azure_data;"
mysql -u root -p -e "CREATE USER 'azure_reader'@'localhost' IDENTIFIED BY 'securepassword';"
mysql -u root -p -e "GRANT SELECT ON azure_data.* TO 'azure_reader'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

Then update your `.env` file:
```
DATABASE=mysql://azure_reader:securepassword@localhost:3306/azure_data
```

## Running the Application

### Development Mode

To run the application in development mode with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

This mode automatically reloads when code changes are detected, making it ideal for development.

### Production Mode

For production deployment, it's recommended to use a production-grade ASGI server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or using Gunicorn with Uvicorn workers:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### Production Configurations

For optimal performance in production:

```bash
# Set number of workers based on CPU cores (2-4 per core)
workers=$(($(nproc) * 2))

# Run with appropriate settings
gunicorn app.main:app \
  --workers $workers \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### Docker Deployment

Create a Docker container for easier deployment:

```bash
# Build the Docker image
docker build -t sql-chat-agent .

# Run the container
docker run -p 8000:8000 --env-file .env sql-chat-agent
```

For production Docker deployments:

```bash
docker run -d \
  --name sql-chat-agent \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  sql-chat-agent
```

### Kubernetes Deployment

For Kubernetes, use the provided manifests in the `deployment/kubernetes` directory:

```bash
# Apply Kubernetes manifests
kubectl apply -f deployment/kubernetes/

# Scale the deployment
kubectl scale deployment/sql-chat-agent --replicas=3
```

## Verifying Installation

Once the application is running, you can verify the installation by accessing the health check endpoint:

```bash
curl http://localhost:8000/check-health
```

You should receive a response similar to:

```json
{
  "status": "Healthy",
  "version": "0.1"
}
```

You can also access the API documentation at:

```
http://localhost:8000/docs
```

### Testing the API

To test a basic query:

```bash
curl -X POST "http://localhost:8000/v1/agent" \
     -H "Content-Type: application/json" \
     -d '{"question": "List the tables in the database"}'
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify the database connection string in the `.env` file
   - Ensure the database is running and accessible
   - Check if the required permissions are granted to the user
   - Test connectivity: `python -c "import sqlalchemy; sqlalchemy.create_engine('your-connection-string').connect()"`

2. **Azure OpenAI API Errors**:
   - Verify the Azure OpenAI endpoint and API key
   - Check if the deployment name is correct
   - Ensure your Azure OpenAI service has enough quota
   - Test the API directly: `curl -X POST "your-endpoint/openai/deployments/your-deployment/completions?api-version=2023-05-15" -H "Content-Type: application/json" -H "api-key: your-key" -d '{"prompt": "Hello", "max_tokens": 5}'`

3. **Vector Store Errors**:
   - Ensure the `data/vector_store` directory exists and is writable
   - Check if the embedding model is accessible
   - Check disk space for vector store data

4. **Module Import Errors**:
   - Ensure all dependencies are correctly installed
   - Verify you're running in the activated virtual environment
   - Try reinstalling dependencies: `pip install -r requirements.txt --force-reinstall`

5. **Permission Issues**:
   - Check file/directory permissions for data storage
   - Verify database user has appropriate SELECT permissions
   - Ensure API keys have correct permission scopes

### Logs

Logs are stored in the `logs` directory. Check the logs for more detailed error information:

```bash
cat logs/app.log
```

For real-time log monitoring:

```bash
tail -f logs/app.log
```

### Advanced Debugging

To enable verbose logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Then start the application
uvicorn app.main:app --reload
```

To debug specific components:

```bash
# Debug database connection
python -c "from app.services.agent import AgentService; from app.services.indexer import IndexerService; indexer = IndexerService(); agent = AgentService(indexer); print('Database connection successful')"

# Test embedding generation
python -c "from app.services.indexer import IndexerService; indexer = IndexerService(); print(indexer.embedding_model.embed_query('test'))"
```

## Upgrade Instructions

To upgrade the application to a newer version:

```bash
# Pull the latest changes
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Restart the application
# If using systemd:
sudo systemctl restart sql-chat-agent
# If using Docker:
docker restart sql-chat-agent
```

## Backup and Recovery

### Database Backup

Regularly backup your database:

```bash
# PostgreSQL
pg_dump -U username -d dbname > backup.sql

# MySQL
mysqldump -u username -p dbname > backup.sql

# SQLite
sqlite3 data/database.db .dump > backup.sql
```

### Vector Store Backup

Backup the vector store directory:

```bash
tar -czvf vector_store_backup.tar.gz data/vector_store/
```

### Recovery Process

To restore from backups:

```bash
# PostgreSQL
psql -U username -d dbname -f backup.sql

# MySQL
mysql -u username -p dbname < backup.sql

# SQLite
sqlite3 data/database.db < backup.sql

# Vector store
tar -xzvf vector_store_backup.tar.gz -C /path/to/restore/
``` 
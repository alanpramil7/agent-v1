"""
Database Service Module

This module provides SQLite database services for the application.
It manages database connections, schema initialization, and CRUD operations
for various entities (wiki, document, website).

The DatabaseService is used by other services to store and retrieve metadata
about indexed content, enabling tracking of processed resources and preventing
redundant processing.
"""

import psycopg2
import sqlite3
from urllib.parse import urlparse
from datetime import datetime
import json

from app.core.config import settings
from app.utils.logger import logger


class DatabaseService:
    """
    Service for managing SQLite database operations.

    This service initializes and manages the SQLite database used for
    tracking metadata about indexed content. It provides methods for:
    - Creating and initializing database tables
    - Adding new records for processed content
    - Checking if content has already been processed

    Each content type (wiki, document, website) has its own table and
    corresponding methods for adding and checking existence.
    """

    def __init__(self):
        """
        Initialize the DatabaseService.

        Sets up the database path and creates required tables if they don't exist.
        """
        # Define database path in the data directory
        # self.db_path = str(settings.data_dir / "rag.db")
        # Initialize tables on service start
        self._initialize_tables()
        # logger.info(f"Database service initialized with database at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a new SQLite database connection.

        Returns:
            sqlite3.Connection: A connection to the SQLite database
        """
        try:
            connection_string = settings.database
            result = urlparse(connection_string)
            username = result.username
            # TODO: Remove hardcoded password
            password = result.password
            database = result.path[1:]
            hostname = result.hostname
            port = result.port
            conn = psycopg2.connect(
                database=database,
                user=username,
                password="qwert@123",
                host=hostname,
                port=port,
            )
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def _initialize_tables(self) -> None:
        """
        Initialize database tables if they don't exist.

        Creates tables for wiki, document, and website metadata.
        Uses 'CREATE TABLE IF NOT EXISTS' to avoid errors if tables already exist.
        """
        logger.debug("Initializing database tables")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                # Create wiki table
                cur.execute("""
                        CREATE TABLE IF NOT EXISTS wiki(
                          organization TEXT,
                          project TEXT,
                          wiki_identifier TEXT,
                          created_at TIMESTAMP,
                          PRIMARY KEY (organization, project, wiki_identifier)
                        )
                        """)
                # Create document table
                cur.execute("""
                        CREATE TABLE IF NOT EXISTS document(
                          file_name TEXT PRIMARY KEY,
                          created_at TIMESTAMP
                        )
                        """)
                # Create website table
                cur.execute("""
                            CREATE TABLE IF NOT EXISTS website(
                            url TEXT PRIMARY KEY,
                            created_at TIMESTAMP
                            )
                            """)
                cur.execute("""
                            CREATE TABLE IF NOT EXISTS agent_conversation(
                            conversation_id TEXT PRIMARY KEY,
                            user_id TEXT,
                            created_at TIMESTAMP
                            )
                            """)
                cur.execute("""
                            CREATE TABLE IF NOT EXISTS agent_messages(
                            message_id TEXT PRIMARY KEY,
                            conversation_id TEXT,
                            sender TEXT,
                            content TEXT,
                            created_at TIMESTAMP
                            )
                            """)

                logger.debug("Database tables initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database tables: {str(e)}")
            raise

    def add_wiki(self, organization: str, project: str, wiki_identifier: str) -> None:
        """
        Add a processed wiki to the database.

        Args:
            organization: Organization name that owns the wiki
            project: Project name that contains the wiki
            wiki_identifier: Unique identifier for the wiki

        Raises:
            sqlite3.Error: If database operation fails
        """
        logger.debug(
            f"Adding wiki to database: {organization}/{project}/{wiki_identifier}"
        )
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                          INSERT OR REPLACE INTO wiki
                          (organization, project, wiki_identifier, created_at)
                          VALUES(?, ?, ?, ?)                      
                          """,
                    (
                        organization,
                        project,
                        wiki_identifier,
                        datetime.utcnow(),
                    ),
                )
                logger.debug(
                    f"Wiki added successfully: {organization}/{project}/{wiki_identifier}"
                )
        except sqlite3.Error as e:
            logger.error(f"Failed to add wiki to database: {str(e)}")
            raise

    def wiki_exists(
        self,
        organization: str,
        project: str,
        wiki_identifier: str,
    ) -> bool:
        """
        Check if a wiki has already been processed.

        Args:
            organization: Organization name that owns the wiki
            project: Project name that contains the wiki
            wiki_identifier: Unique identifier for the wiki

        Returns:
            bool: True if wiki exists in database, False otherwise

        Raises:
            sqlite3.Error: If database operation fails
        """
        logger.debug(
            f"Checking if wiki exists: {organization}/{project}/{wiki_identifier}"
        )
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT 1 FROM wiki 
                    WHERE organization = ? 
                    AND project = ? 
                    AND wiki_identifier = ?
                    LIMIT 1
                    """,
                    (organization, project, wiki_identifier),
                )
                result = cur.fetchone()
                exists = bool(result)
                logger.debug(f"Wiki exists: {exists}")
                return exists
        except sqlite3.Error as e:
            logger.error(f"Failed to check if wiki exists: {str(e)}")
            raise

    def add_document(self, file_name: str) -> None:
        """
        Add a processed document to the database.

        Args:
            file_name: Name of the processed document file

        Raises:
            sqlite3.Error: If database operation fails
        """
        logger.debug(f"Adding document to database: {file_name}")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                            INSERT OR REPLACE INTO document
                            (file_name, created_at)
                            VALUES (?, ?)
                            """,
                    (file_name, datetime.utcnow()),
                )
                logger.debug(f"Document added successfully: {file_name}")
        except sqlite3.Error as e:
            logger.error(f"Failed to add document to database: {str(e)}")
            raise

    def document_exists(
        self,
        file_name: str,
    ) -> bool:
        """
        Check if a document has already been processed.

        Args:
            file_name: Name of the document file to check

        Returns:
            bool: True if document exists in database, False otherwise

        Raises:
            sqlite3.Error: If database operation fails
        """
        logger.debug(f"Checking if document exists: {file_name}")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT 1 FROM document 
                    WHERE file_name = ? 
                    LIMIT 1
                    """,
                    (file_name,),
                )
                result = cur.fetchone()
                exists = bool(result)
                logger.debug(f"Document exists: {exists}")
                return exists
        except sqlite3.Error as e:
            logger.error(f"Failed to check if document exists: {str(e)}")
            raise

    def add_website(self, url: str) -> None:
        """
        Add a processed website to the database.

        Args:
            url: URL of the processed website

        Raises:
            sqlite3.Error: If database operation fails
        """
        logger.debug(f"Adding website to database: {url}")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                            INSERT OR REPLACE INTO website
                            (url, created_at)
                            VALUES(?, ?)
                            """,
                    (
                        url,
                        datetime.utcnow(),
                    ),
                )
                logger.debug(f"Website added successfully: {url}")
        except sqlite3.Error as e:
            logger.error(f"Failed to add website to database: {str(e)}")
            raise

    def website_exists(
        self,
        url: str,
    ) -> bool:
        """
        Check if a website has already been processed.

        Args:
            url: URL of the website to check

        Returns:
            bool: True if website exists in database, False otherwise

        Raises:
            sqlite3.Error: If database operation fails
        """
        logger.debug(f"Checking if website exists: {url}")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                        SELECT 1 FROM website 
                        WHERE url = ? 
                        LIMIT 1
                        """,
                    (url,),
                )
                result = cur.fetchone()
                exists = bool(result)
                logger.debug(f"Website exists: {exists}")
                return exists
        except sqlite3.Error as e:
            logger.error(f"Failed to check if website exists: {str(e)}")
            raise

    def add_conversation(self, conversation_id: str, user_id: str):
        """"""
        logger.debug("Adding conversatioh to databse.")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO agent_conversation
                    (conversation_id, user_id, created_at)
                    VALUES(%s, %s, %s)
                    """,
                    (
                        conversation_id,
                        user_id,
                        datetime.utcnow(),
                    ),
                )

        except psycopg2.Error as e:
            logger.error(f"Failed to add conversation detail to the databse: {e}")
            raise

    def conversation_exists(self, conversation_id: str) -> bool:
        """"""
        logger.debug(f"Checking if conversation exists: {conversation_id}")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT 1 FROM agent_conversation
                    WHERE conversation_id = %s
                    LIMIT 1
                    """,
                    (conversation_id,),
                )
                result = cur.fetchone()
                exists = bool(result)
                return exists
        except psycopg2.Error as e:
            logger.error(f"Failed to check if conversation exists: {str(e)}")
            raise

    def add_message(
        self,
        message_id: str,
        conversation_id: str,
        sender: str,
        content: str | dict,
    ):
        """"""
        logger.debug("Adding message to database.")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()

                # Convert dict to JSON string if needed
                if isinstance(content, dict):
                    content = json.dumps(content)

                cur.execute(
                    """
                    INSERT INTO agent_messages
                    (message_id, conversation_id, sender, content,  created_at)
                    VALUES(%s, %s, %s, %s, %s)
                    """,
                    (
                        message_id,
                        conversation_id,
                        sender,
                        content,
                        datetime.utcnow(),
                    ),
                )
        except psycopg2.Error as e:
            logger.debug(f"Failed to add messages in the database: {e}")
            raise

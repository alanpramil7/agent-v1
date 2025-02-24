import sqlite3
from datetime import datetime

from app.core.config import settings
from app.utils.logger import logger


class DatabaseService:
    def __init__(self):
        self.db_path = str(settings.data_dir / "rag.db")
        self._initialize_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_tables(self):
        logger.debug("Initializing tables.")
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                    CREATE TABLE IF NOT EXISTS wiki(
                      organization TEXT,
                      project TEXT,
                      wiki_identifier TEXT,
                      created_at TIMESTAMP
                    )
                    """)
            cur.execute("""
                    CREATE TABLE IF NOT EXISTS document(
                      file_name TEXT,
                      created_at TIMESTAMP
                    )
                    """)

    def add_wiki(self, organization: str, project: str, wiki_identifier: str):
        """"""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                      INSERT INTO wiki
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

    def wiki_exists(
        self,
        organization: str,
        project: str,
        wiki_identifier: str,
    ) -> bool:
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
            return bool(result)

    def add_document(self, file_name: str):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                        INSERT INTO document
                        (file_name, created_at)
                        VALUES (?, ?)
                        """,
                (file_name, datetime.utcnow()),
            )

    def document_exists(
        self,
        file_name: str,
    ) -> bool:
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
            return bool(result)

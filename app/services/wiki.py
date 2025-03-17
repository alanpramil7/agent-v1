"""
Wiki Service Module

This module provides services for processing Azure DevOps Wiki content.
It handles wiki page retrieval, content extraction, chunking, and indexing into the
vector database for later retrieval and querying.

The WikiService supports recursive traversal of wiki pages, concurrent processing,
and ensures proper error handling and deduplication of wiki content processing.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional

import aiohttp
from langchain_core.documents import Document

from app.models.wiki import WikiPage
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.utils.logger import logger


class WikiService:
    """
    Service for processing and indexing Azure DevOps Wiki content.

    This service handles the complete lifecycle of wiki processing:
    - Authenticating with Azure DevOps API
    - Retrieving wiki pages recursively
    - Extracting content from wiki pages
    - Converting wiki content to documents
    - Adding documents to the vector store
    - Recording processed wikis in the database

    It works with the IndexerService for vector operations and
    DatabaseService for tracking processed wikis.
    """

    def __init__(
        self,
        organization: str,
        project: str,
        wiki_identifier: str,
        pat: str,
        database: DatabaseService,
        indexer: IndexerService,
    ):
        """
        Initialize the WikiService.

        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            wiki_identifier: Unique identifier for the wiki
            pat: Personal Access Token for Azure DevOps
            database: Service for tracking processed wikis
            indexer: Service for vector indexing operations
        """
        self.database = database
        self.indexer = indexer
        self.organization = organization
        self.project = project
        self.wiki_identifier = wiki_identifier
        self.personal_access_token = pat
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis/wiki/wikis/{wiki_identifier}/pages"
        self.auth = aiohttp.BasicAuth("", self.personal_access_token)
        self.api_version = "7.1"
        logger.debug(f"Wiki service initialized for wiki: {wiki_identifier}")

    async def _fetch_wiki_pages(self) -> Optional[List[WikiPage]]:
        """
        Fetch all wiki pages from Azure DevOps Wiki.

        Retrieves the complete wiki structure recursively, including content
        for all pages.

        Returns:
            Optional[List[WikiPage]]: List of wiki pages with content, or None if retrieval fails
        """
        logger.debug(f"Fetching wiki pages for {self.wiki_identifier}")
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                # Get the root page first with recursive retrieval
                params = {
                    "path": "/",
                    "recursionLevel": "full",
                    "includeContent": "true",
                    "api-version": self.api_version,
                }

                # Define timeout to prevent hanging on large wikis
                timeout = aiohttp.ClientTimeout(total=300)  # 5-minute timeout
                async with session.get(
                    self.base_url, params=params, timeout=timeout
                ) as response:
                    if response.status == 200:
                        wiki_tree = await response.json()
                        pages = await self._process_wiki_tree(wiki_tree, session)
                        logger.info(f"Successfully fetched {len(pages)} wiki pages")
                        return pages
                    else:
                        response_text = await response.text()
                        logger.error(
                            f"Failed to fetch wiki pages. Status: {response.status}, Response: {response_text[:200]}"
                        )
                        return None

        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error fetching wiki pages: {str(e)}")
            return None
        except asyncio.TimeoutError:
            logger.error("Timeout fetching wiki pages")
            return None
        except Exception as e:
            logger.error(f"Error fetching wiki pages: {str(e)}", exc_info=True)
            return None

    async def _process_wiki_tree(
        self, page: dict, session: aiohttp.ClientSession
    ) -> List[WikiPage]:
        """
        Process wiki tree and extract pages recursively.

        Args:
            page: Dictionary representing a wiki page from the API
            session: Active HTTP session for additional content retrieval

        Returns:
            List[WikiPage]: List of wiki pages with content
        """
        pages = []

        # Extract page data
        page_path = page.get("path", "/")
        content = page.get("content", "")

        # Fetch content if not included in the tree response
        if not content:
            content = await self._fetch_page_content(page_path, session)

        # Create WikiPage object
        wiki_page = WikiPage(
            page_path=page_path,
            content=content,
            remote_url=page.get("remoteUrl", ""),
        )
        logger.debug(f"Processed wiki page: {wiki_page.page_path}")
        pages.append(wiki_page)

        # Recursively process subpages
        for subpage in page.get("subPages", []):
            subpage_results = await self._process_wiki_tree(subpage, session)
            pages.extend(subpage_results)

        return pages

    async def _fetch_page_content(
        self, page_path: str, session: aiohttp.ClientSession
    ) -> str:
        """
        Fetch the content of a specific wiki page.

        Args:
            page_path: Path of the wiki page to fetch
            session: Active HTTP session for content retrieval

        Returns:
            str: Content of the wiki page, or empty string if retrieval fails
        """
        logger.debug(f"Fetching content for page: {page_path}")
        try:
            params = {
                "path": page_path,
                "includeContent": "true",
                "api-version": self.api_version,
            }
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    page_data = await response.json()
                    content = page_data.get("content", "")
                    logger.debug(
                        f"Fetched content for page: {page_path} ({len(content)} characters)"
                    )
                    return content
                else:
                    response_text = await response.text()
                    logger.error(
                        f"Failed to fetch content for page {page_path}. Status: {response.status}, Response: {response_text[:200]}"
                    )
                    return ""
        except Exception as e:
            logger.error(f"Error fetching content for page {page_path}: {str(e)}")
            return ""

    async def process_wiki(
        self,
        organization: str,
        project: str,
        wiki_identifier: str,
    ) -> Dict[str, Any]:
        """
        Process wiki pages and index them in the vector database.

        Args:
            organization: Azure DevOps organization name
            project: Azure DevOps project name
            wiki_identifier: Unique identifier for the wiki

        Returns:
            Dict[str, Any]: Processing status and metadata
        """
        logger.info(f"Processing wiki: {organization}/{project}/{wiki_identifier}")

        try:
            # Check if wiki has already been processed
            if self.database.wiki_exists(organization, project, wiki_identifier):
                logger.info(f"Wiki is already processed: {wiki_identifier}")
                return {
                    "status": "Wiki already processed",
                    "wiki_identifier": wiki_identifier,
                }

            # Validate indexer is initialized
            if not self.indexer.vector_store or not self.indexer.text_splitter:
                logger.error("Indexer not initialized properly for wiki processing")
                return {
                    "status": "Failed",
                    "error": "Vector store or text splitter not initialized",
                }

            # Fetch all wiki pages
            pages = await self._fetch_wiki_pages()
            if not pages:
                logger.warning(f"No pages found in wiki: {wiki_identifier}")
                return {"status": "No pages found"}

            # Track processing results
            processed_pages = []
            failed_pages = []

            total_pages = len(pages)
            logger.info(f"Starting to process {total_pages} wiki pages")

            # Define a function to process a single page
            async def process_single_page(page: WikiPage, idx: int) -> None:
                """Process a single wiki page."""
                try:
                    logger.debug(
                        f"Processing page {idx}/{total_pages}: {page.page_path}"
                    )

                    # Skip empty pages
                    if not page.content.strip():
                        logger.warning(f"Page {page.page_path} is empty - skipping")
                        return

                    content_length = len(page.content)
                    logger.debug(
                        f"Page {page.page_path} content length: {content_length} characters"
                    )

                    logger.debug("Clenaing image tags.")
                    content = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", page.content)

                    if content == "":
                        logger.warning(f"Page {page.page_path} is empty - skipping")
                        return

                    # Create document with metadata
                    doc = Document(
                        page_content=f"{page.page_path}\n{content}",
                        metadata={
                            "source": f"wiki_{page.page_path}",
                            "organization": organization,
                            "project": project,
                            "wiki_identifier": wiki_identifier,
                            "remote_url": page.remote_url,
                        },
                    )

                    # Split document into chunks for vectorization
                    chunks = self.indexer.text_splitter.split_documents([doc])

                    if not chunks:
                        logger.warning(
                            f"No chunks generated for page {page.page_path} - skipping"
                        )
                        return

                    # Index the chunks
                    if self.indexer.vector_store:
                        self.indexer.vector_store.add_documents(chunks)
                        processed_pages.append(page.page_path)
                        logger.debug(
                            f"Successfully processed and indexed page: {page.page_path} ({len(chunks)} chunks)"
                        )
                    else:
                        logger.error("Vector store not initialized")
                        failed_pages.append(page.page_path)
                        logger.error(
                            f"Failed to process page {page.page_path} due to uninitialized vector store"
                        )

                except Exception as e:
                    logger.error(
                        f"Error processing page {page.page_path}: {str(e)}",
                        exc_info=True,
                    )
                    failed_pages.append(page.page_path)

            # Process all pages concurrently
            tasks = [
                process_single_page(page, idx) for idx, page in enumerate(pages, 1)
            ]
            await asyncio.gather(*tasks)

            # Log processing summary
            logger.info(
                f"Wiki processing completed. Successfully processed: {len(processed_pages)} pages, Failed: {len(failed_pages)} pages"
            )
            if failed_pages:
                logger.warning(
                    f"Failed pages: {', '.join(failed_pages[:10])}{'...' if len(failed_pages) > 10 else ''}"
                )

            # Return status and record in database if successful
            if failed_pages:
                return {
                    "status": "Completed with errors",
                    "processed_pages": len(processed_pages),
                    "failed_pages": len(failed_pages),
                    "wiki_identifier": wiki_identifier,
                }
            else:
                # Record successful processing in database
                self.database.add_wiki(organization, project, wiki_identifier)
                return {
                    "status": "Successfully processed",
                    "processed_pages": len(processed_pages),
                    "failed_pages": 0,
                    "wiki_identifier": wiki_identifier,
                }

        except Exception as e:
            logger.error(
                f"Error processing wiki {wiki_identifier}: {str(e)}", exc_info=True
            )
            return {
                "status": "Failed",
                "error": str(e),
                "wiki_identifier": wiki_identifier,
            }

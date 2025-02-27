"""
Website Service Module

This module provides services for processing website content from URLs.
It handles website crawling, text extraction, chunking, and indexing into the
vector database for later retrieval and querying.

The WebsiteService supports sitemap-based discovery of page URLs and ensures
proper validation, error handling, and deduplication of website processing.
"""

import asyncio
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from langchain_community.document_loaders import WebBaseLoader
from pydantic import HttpUrl

from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.utils.logger import logger


class WebsiteService:
    """
    Service for processing and indexing website content.

    This service handles the complete lifecycle of website processing:
    - Discovering website pages via sitemap.xml
    - Loading and extracting content from web pages
    - Splitting content into chunks
    - Adding content chunks to the vector store
    - Recording processed websites in the database

    It works with the IndexerService for vector operations and
    DatabaseService for tracking processed websites.
    """

    def __init__(
        self,
        indexer: IndexerService,
        database: DatabaseService,
    ):
        """
        Initialize the WebsiteService.

        Args:
            indexer: Service for vector indexing operations
            database: Service for tracking processed websites
        """
        self.indexer = indexer
        self.database = database
        logger.debug("Website service initialized")

    async def _fetch_sitemap(self, base_url: HttpUrl) -> List[str]:
        """
        Fetch and parse the website's sitemap.xml to discover URLs.

        Args:
            base_url: Base URL of the website

        Returns:
            List[str]: List of URLs found in the sitemap, or just the base URL if no sitemap

        Note:
            If the sitemap is not found or cannot be parsed, returns a list
            containing only the base URL as a fallback.
        """
        logger.debug(f"Fetching sitemap for URL: {base_url}")
        sitemap_url = urljoin(str(base_url), "sitemap.xml")

        try:
            # Use a timeout to prevent hanging on slow websites
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(sitemap_url)
                response.raise_for_status()

            # Parse the XML sitemap
            root = ET.fromstring(response.content)
            urls = [
                loc.text
                for loc in root.findall(
                    ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                )
                if loc.text and not loc.text.endswith(".pdf")
            ]

            if not urls:
                logger.warning(f"No valid URLs found in sitemap for {base_url}")
                return [str(base_url)]

            logger.debug(f"Found {len(urls)} URLs in sitemap for {base_url}")
            return urls

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"Failed to fetch sitemap for {base_url}: HTTP {e.response.status_code}"
            )
            return [str(base_url)]
        except httpx.RequestError as e:
            logger.warning(
                f"Connection error while fetching sitemap for {base_url}: {str(e)}"
            )
            return [str(base_url)]
        except ET.ParseError as e:
            logger.warning(f"XML parsing error in sitemap for {base_url}: {str(e)}")
            return [str(base_url)]
        except Exception as e:
            logger.warning(
                f"Unexpected error fetching sitemap for {base_url}: {str(e)}"
            )
            return [str(base_url)]

    async def _process_url(self, url: str) -> Optional[int]:
        """
        Process a single URL, extracting content and adding to vector store.

        Args:
            url: URL to process

        Returns:
            Optional[int]: Number of chunks added to vector store, or None if failed
        """
        logger.debug(f"Processing URL: {url}")
        try:
            # Load content from the URL
            loader = WebBaseLoader(str(url))
            docs = loader.load()

            if not docs:
                logger.warning(f"No content found at URL: {url}")
                return None

            # Split content into chunks for indexing
            chunks = self.indexer.text_splitter.split_documents(docs)
            if not chunks:
                logger.warning(f"No chunks generated for URL: {url}")
                return None

            # Add chunks to vector store
            logger.debug(
                f"Adding {len(chunks)} chunks from URL: {url} to vector database"
            )
            self.indexer.vector_store.add_documents(chunks)

            # Record website as processed in database
            self.database.add_website(url)
            logger.info(f"Successfully processed URL: {url} with {len(chunks)} chunks")

            return len(chunks)

        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return None

    async def process_website(self, url: HttpUrl) -> Dict[str, Any]:
        """
        Process an entire website, starting from a base URL.

        Args:
            url: Base URL of the website to process

        Returns:
            Dict[str, Any]: Processing status and metadata
        """
        logger.info(f"Processing website: {url}")

        try:
            # Discover URLs from sitemap
            urls = await self._fetch_sitemap(url)
            logger.info(f"Found {len(urls)} URLs to process for website: {url}")

            # Process all URLs concurrently
            tasks = [self._process_url(url) for url in urls]
            results = await asyncio.gather(*tasks)

            # Count successfully processed URLs
            successful_urls = sum(1 for result in results if result is not None)
            total_chunks = sum(result for result in results if result is not None)

            logger.info(
                f"Completed website processing: {url}, {successful_urls}/{len(urls)} pages processed"
            )

            return {
                "status": "success",
                "processed_urls": successful_urls,
                "total_urls": len(urls),
                "total_chunks": total_chunks,
                "message": f"Successfully processed {successful_urls} pages from {url}",
            }

        except Exception as e:
            logger.error(f"Error processing website {url}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing website: {str(e)}",
            }

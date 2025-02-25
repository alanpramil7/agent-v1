import asyncio
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import httpx
from langchain_community.document_loaders import WebBaseLoader
from pydantic import HttpUrl

from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.utils.logger import logger


class WebsiteService:
    def __init__(
        self,
        indexer: IndexerService,
        database: DatabaseService,
    ):
        self.indexer = indexer
        self.database = database

    async def _fetch_sitemap(self, base_url: HttpUrl):
        logger.debug(f"Fetching sitemap for url: {base_url}")
        sitemap_url = urljoin(str(base_url), "sitemap.xml")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(sitemap_url)
                response.raise_for_status()

            root = ET.fromstring(response.content)
            urls = [
                loc.text
                for loc in root.findall(
                    ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                )
                if loc.text and not loc.text.endswith(".pdf")
            ]
            logger.debug(f"Urls found {len(urls)}")
            return urls

        except Exception as e:
            logger.warning(f"No sitemap found for {base_url}: {e}")
            return [base_url]

    async def _process_url(self, url: str):
        logger.debug(f"Processing url: {url}")
        try:
            loader = WebBaseLoader(str(url))
            docs = loader.load()

            if not docs:
                logger.warning("No document found on the website.")
                return

            chunks = self.indexer.text_splitter.split_documents(docs)
            logger.debug("Adding chunks into vector database")
            # await self.indexer.vector_store.aadd_documents(chunks)
            self.database.add_website(url)
            logger.debug(f"Added {len(chunks)} into vectordb.")

        except Exception as e:
            logger.error(f"Error while processing url {url} :{e}")
            return

    async def process_website(self, url: str):
        urls = await self._fetch_sitemap(url)

        # Process all URLs concurrently
        tasks = [self._process_url(url) for url in urls]
        await asyncio.gather(*tasks)

        return {
            "status": "success",
            "message": f"Added {len(urls)} into vectorstore.",
        }

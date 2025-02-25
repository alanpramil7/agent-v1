from typing import List, Optional

import aiohttp
from langchain_core.documents import Document

from app.models.wiki import WikiPage
from app.services.database import DatabaseService
from app.services.indexer import IndexerService
from app.utils.logger import logger


class WikiService:
    def __init__(
        self,
        organization: str,
        project: str,
        wiki_identifier: str,
        pat: str,
        database: DatabaseService,
        indexer: IndexerService,
    ):
        self.database = database
        self.indexer = indexer
        self.organization = organization
        self.project = project
        self.wiki_identifier = wiki_identifier
        self.personal_access_token = pat
        self.base_url = f"https://dev.azure.com/{organization}/{project}/_apis/wiki/wikis/{wiki_identifier}/pages"
        self.auth = aiohttp.BasicAuth("", self.personal_access_token)
        self.api_version = "7.1"

    async def _fetch_wiki_pages(self) -> Optional[List[WikiPage]]:
        """Fetch all wiki pages from Azure DevOps Wiki."""
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                # Get the root page first
                params = {
                    "path": "/",
                    "recursionLevel": "full",
                    "includeContent": "true",
                    "api-version": self.api_version,
                }

                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        wiki_tree = await response.json()
                        pages = await self._process_wiki_tree(wiki_tree, session)
                        return pages
                    else:
                        logger.error(
                            f"Failed to fetch wiki pages. Status: {response.status}"
                        )
                        return None

        except Exception as e:
            logger.error(f"Error fetching wiki pages: {str(e)}")
            return None

    async def _process_wiki_tree(
        self, page: dict, session: aiohttp.ClientSession
    ) -> List[WikiPage]:
        """Process wiki tree and extract pages."""
        pages = []

        page_path = page.get("path", "/")
        content = page.get("content", "")

        if not content:
            content = await self._fetch_page_content(page_path, session)

        wiki_page = WikiPage(
            page_path=page_path,
            content=content,
            remote_url=page.get("remoteUrl"),
        )
        logger.debug(f"Fetched page: {wiki_page.page_path}")
        pages.append(wiki_page)

        for subpage in page.get("subPages", []):
            subpage_results = await self._process_wiki_tree(subpage, session)
            pages.extend(subpage_results)

        return pages

    async def _fetch_page_content(
        self, page_path: str, session: aiohttp.ClientSession
    ) -> str:
        """Fetch the content of a specific wiki page."""
        params = {
            "path": page_path,
            "includeContent": "true",
            "api-version": self.api_version,
        }
        async with session.get(self.base_url, params=params) as response:
            if response.status == 200:
                page_data = await response.json()
                return page_data.get("content", "")
            else:
                logger.error(
                    f"Failed to fetch content for page {page_path}. Status: {response.status}"
                )
                return ""

    async def process_wiki(
        self,
        organization: str,
        project: str,
        wiki_identifier: str,
    ) -> dict:
        """Process wiki pages synchronously and update database."""
        try:
            if self.database.wiki_exists(organization, project, wiki_identifier):
                logger.debug(f"Wiki is already processed : {wiki_identifier}")
                return {
                    "status": "Wiki already processed.",
                }

            pages = await self._fetch_wiki_pages()
            if not pages:
                logger.debug("No pages found in the wiki.")
                return {"status": "No pages found."}

            processed_pages = []
            failed_pages = []

            total_pages = len(pages)
            logger.debug(f"Starting to process {total_pages} wiki pages")

            for idx, page in enumerate(pages, 1):
                try:
                    logger.debug(
                        f"Processing page {idx}/{total_pages}: {page.page_path}"
                    )

                    if not page.content.strip():
                        logger.warning(f"Page {page.page_path} is empty - skipping")
                        continue

                    content_length = len(page.content)
                    logger.debug(
                        f"Page {page.page_path} content length: {content_length} characters"
                    )

                    doc = Document(
                        page_content=f"{page.page_path}\n{page.content}",
                        metadata={
                            "source": f"wiki_{page.page_path}",
                            "organization": organization,
                            "project": project,
                        },
                    )

                    if self.indexer.vector_store:
                        await self.indexer.vector_store.aadd_documents([doc])
                        processed_pages.append(page.page_path)
                        logger.debug(
                            f"Successfully processed and indexed page: {page.page_path}"
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

            logger.debug(
                f"Wiki processing completed. Successfully processed: {len(processed_pages)} pages, Failed: {len(failed_pages)} pages"
            )
            if failed_pages:
                logger.warning(f"Failed pages: {', '.join(failed_pages)}")

            if failed_pages:
                return {
                    "status": "Completed with errors",
                    "processed_pages": len(processed_pages),
                    "failed_pages": len(failed_pages),
                }
            else:
                self.database.add_wiki(organization, project, wiki_identifier)
                return {
                    "status": "Successfully processed",
                    "processed_pages": len(processed_pages),
                    "failed_pages": 0,
                }

        except Exception as e:
            logger.error(f"Error processing wiki: {str(e)}")
            return {"status": "Failed", "error": str(e)}

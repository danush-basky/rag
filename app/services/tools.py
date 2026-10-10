from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import logger
from app.services.vector import vector_service

settings = get_settings()


class EducationalRetrievalInput(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Clean, keyword-dense concept query. Must contain core topic names, chapter titles, "
            "theorems, or principles to look up in the syllabus (e.g., 'Application of Integrals area under curve theory', "
            "'Carnot cycle second law thermodynamics', 'Markovnikov addition mechanism'). "
            "Do NOT use this for calculating values or solving numerical problems."
        ),
    )
    subject: str | None = Field(
        None,
        description=(
            "The broad discipline: strictly one of 'Physics', 'Chemistry', 'Mathematics', or 'Biology'. "
            "Pass null if undetermined or interdisciplinary."
        ),
    )


@tool(
    "retrieve_study_material",
    args_schema=EducationalRetrievalInput,
    description=settings.RETRIEVE_STUDY_MATERIAL_DESC,
)
async def retrieve_study_material(
    query: str,
    config: RunnableConfig,
    subject: str | None = None,
) -> str:
    configurable = config.get("configurable", {})
    exam = configurable.get("exam")
    filter_dict: dict[str, Any] = {}
    if exam:
        filter_dict["exam"] = str(exam).strip().upper()
    if subject:
        filter_dict["subject"] = subject.strip().capitalize()

    logger.info(f"🔍 Executing vector retrieval: '{query}' | Filters: {filter_dict}")

    try:
        docs = await vector_service.search(
            query=query,
            k=settings.TOP_K_RETRIEVAL,
            filters=filter_dict if filter_dict else None,
            rerank=settings.RERANKER_ENABLE,
            reranked_k=settings.RERANK_TOP_K,
            score_threshold=settings.RERANK_SCORE_THRESHOLD,
        )

        if not docs:
            return (
                "NO_DOCUMENTS_FOUND: No exact matches found for the query in the knowledge base. "
                "Try rephrasing with alternative technical keywords or removing the subject filter."
            )

        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            meta = doc.metadata or {}
            source_info = (
                f"Source: {meta.get('source', 'Unknown')} | "
                f"Exam: {meta.get('exam', 'General')} | "
                f"Subject: {meta.get('subject', 'General')} | "
                f"Topic: {meta.get('topic', 'General')}"
            )
            formatted_docs.append(
                f'<document id="{i}" {source_info}>\n{doc.page_content}\n</document>'
            )

        return "\n\n".join(formatted_docs)

    except Exception as exc:
        logger.error(f"Error during retrieval: {exc}", exc_info=True)
        return f"RETRIEVAL_ERROR: Failed to retrieve study material: {exc!s}. Try rephrasing or clearing filters."

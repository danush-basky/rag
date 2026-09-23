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


@tool("retrieve_study_material", args_schema=EducationalRetrievalInput)
async def retrieve_study_material(
    query: str,
    config: RunnableConfig,
    subject: str | None = None,
) -> str:
    """Retrieves authoritative textbook theory, definitions, derivations, and conceptual syllabus notes.

    STRICT USAGE GATE:
    ✓ CALL THIS ONLY FOR CONCEPTUAL & THEORETICAL QUERIES:
      - Explaining a concept, topic, or chapter (e.g., 'What is Application of Integrals?', 'Explain Faraday's laws').
      - Formal definitions, qualitative principles, and curriculum overviews.
      - Mathematical and physical derivations (e.g., 'Derive mirror formula').

    ✗ DO NOT CALL THIS FOR ANY PROBLEM-SOLVING OR NUMERICAL TASKS:
      - Numerical problems with given values (e.g., 'Find the area between y^2 = 4ax and x^2 = 4ay', 'A block of mass 5kg...').
      - Step-by-step mathematical calculations, integration evaluations, or algebraic simplification.
      - Any Multiple Choice Questions (MCQs), whether numerical or theoretical.
      - Solve all problem-based questions directly from core first principles without calling this tool.

    Returns:
        Authoritative textbook excerpts, definitions, and theory tagged in XML format.
    """
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

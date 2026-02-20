from uuid import UUID
from typing import Any, Optional
from langchain_core.tools import tool


def create_agent_tools(context: dict):
    """Create tools bound to the request context."""

    @tool
    async def search_knowledge(query: str, company_id: Optional[str] = None, limit: int = 5) -> str:
        """Search transcripts and use cases by semantic similarity. Use when user asks about content, themes, or specific topics."""
        kb = context.get("knowledge_base")
        if not kb:
            return "Knowledge base not available."
        results = kb.search_all(query, limit=limit, company_id=company_id)
        parts = []
        for r in results.get("transcripts", [])[:3]:
            parts.append(f"[Transcript chunk] {r['payload'].get('text', '')[:500]}...")
        for r in results.get("use_cases", [])[:3]:
            p = r["payload"]
            parts.append(f"[Use case: {p.get('title')}] {p.get('description', '')[:300]}...")
        return "\n\n".join(parts) if parts else "No relevant results found."

    @tool
    async def list_transcripts(company_id: str) -> str:
        """List transcripts for a company. Use when user asks what transcripts exist."""
        service = context.get("transcript_service")
        if not service:
            return "Transcript service not available."
        items, total = await service.list_by_company(UUID(company_id), skip=0, limit=50)
        if not items:
            return f"No transcripts found for company {company_id}."
        lines = [f"- {t.filename} (id={t.id}, status={t.status})" for t in items]
        return "\n".join(lines)

    @tool
    async def list_use_cases(company_id: str, status: Optional[str] = None) -> str:
        """List use cases for a company. Optionally filter by status: new, under_review, approved, in_progress, completed, archived."""
        service = context.get("use_case_service")
        if not service:
            return "Use case service not available."
        from app.models.enums import UseCaseStatus
        status_enum = None
        if status:
            try:
                status_enum = UseCaseStatus(status)
            except ValueError:
                pass
        items, total = await service.list_with_filters(
            company_id=UUID(company_id), status=status_enum, skip=0, limit=50
        )
        if not items:
            return f"No use cases found for company {company_id}."
        lines = [f"- {uc.title} (id={uc.id}, status={uc.status})" for uc in items]
        return "\n".join(lines)

    @tool
    async def get_transcript_summary(transcript_id: str) -> str:
        """Get a summary of a transcript's content (first 2000 chars)."""
        service = context.get("transcript_service")
        if not service:
            return "Transcript service not available."
        t = await service.get_transcript(UUID(transcript_id))
        if not t:
            return f"Transcript {transcript_id} not found."
        preview = (t.raw_text or "")[:2000]
        return f"Transcript: {t.filename}\nStatus: {t.status}\nPreview:\n{preview}..."

    @tool
    async def create_use_case(
        company_id: str,
        title: str,
        description: str,
        transcript_id: Optional[str] = None,
        expected_benefit: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """Create a new use case for a company."""
        service = context.get("use_case_service")
        if not service:
            return "Use case service not available."
        from app.schemas import UseCaseCreate
        data = UseCaseCreate(
            company_id=UUID(company_id),
            title=title,
            description=description,
            transcript_id=UUID(transcript_id) if transcript_id else None,
            expected_benefit=expected_benefit,
            tags=tags,
        )
        uc = await service.create_use_case(data)
        await service.commit()
        return f"Created use case: {uc.title} (id={uc.id})"

    @tool
    async def update_use_case(
        use_case_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        expected_benefit: Optional[str] = None,
    ) -> str:
        """Update an existing use case."""
        service = context.get("use_case_service")
        if not service:
            return "Use case service not available."
        from app.schemas import UseCaseUpdate
        data = UseCaseUpdate(title=title, description=description, expected_benefit=expected_benefit)
        uc = await service.update_use_case(UUID(use_case_id), data)
        await service.commit()
        if not uc:
            return f"Use case {use_case_id} not found."
        return f"Updated use case: {uc.title}"

    @tool
    async def list_companies() -> str:
        """List all companies."""
        service = context.get("company_service")
        if not service:
            return "Company service not available."
        items, total = await service.list_companies(skip=0, limit=50)
        if not items:
            return "No companies found."
        lines = [f"- {c.name} (id={c.id})" for c in items]
        return "\n".join(lines)

    return [
        search_knowledge,
        list_transcripts,
        list_use_cases,
        get_transcript_summary,
        create_use_case,
        update_use_case,
        list_companies,
    ]

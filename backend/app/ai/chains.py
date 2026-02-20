from typing import List, Optional

from app.config import settings
from app.clients import get_chat_llm
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

class ExtractedUseCase(BaseModel):
    title: str = Field(description="Short, clear title of the use case")
    description: str = Field(description="Detailed description of the problem or opportunity")
    expected_benefit: Optional[str] = Field(None, description="Business value this creates")
    tags: List[str] = Field(default_factory=list, description="2-5 topic tags")
    confidence_score: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description=(
            "1.0 = explicitly stated as a use case. "
            "0.7 = clearly a problem but stated implicitly. "
            "0.4 = vague mention, uncertain if actionable. "
            "0.2 = barely suggested."
        )
    )

class ExtractionResult(BaseModel):
    use_cases: List[ExtractedUseCase]

MAP_SYSTEM = """You are an expert analyst extracting actionable use cases from workshop transcripts.
A use case is a specific, concrete business or technology opportunity discussed.
Be conservative: vague or tangential mentions score below 0.5.
Do NOT invent use cases not present in the text."""

REDUCE_SYSTEM = """You are merging use cases extracted from different sections of the same transcript.
Merge obvious duplicates (same underlying idea). Combine details from multiple mentions.
Raise confidence_score if a use case was mentioned multiple times. Keep distinct ones separate.
CRITICAL: Do NOT output any use case that is semantically similar to one already in the "already_extracted" list.
Treat "already_extracted" as the canonical list of use cases already produced—do not duplicate them."""

def create_extraction_chain(
    model: str | None = None,
    temperature: float = 0.3,
) -> any:  # returns Runnable
    if not settings.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    llm = get_chat_llm(model=model, temperature=temperature)

    parser = PydanticOutputParser(pydantic_object=ExtractionResult)

    prompt = PromptTemplate(
        template=(
            "{system_prompt}\n\n"
            "{format_instructions}\n\n"
            "Transcript excerpt:\n{text}"
        ),
        input_variables=["text"],
        partial_variables={
            "system_prompt": MAP_SYSTEM,
            "format_instructions": parser.get_format_instructions(),
        },
    )

    return prompt | llm | parser

def create_reduction_chain(
    model: str | None = None,
    temperature: float = 0.3,
) -> any:
    if not settings.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    llm = get_chat_llm(model=model, temperature=temperature)

    parser = PydanticOutputParser(pydantic_object=ExtractionResult)

    prompt = PromptTemplate(
        template=(
            "{system_prompt}\n\n"
            "{format_instructions}\n\n"
            "ALREADY EXTRACTED (do not duplicate):\n{already_extracted}\n\n"
            "New use cases from this batch (merge/deduplicate against above):\n{text}"
        ),
        input_variables=["text", "already_extracted"],
        partial_variables={
            "system_prompt": REDUCE_SYSTEM,
            "format_instructions": parser.get_format_instructions(),
        },
    )

    return prompt | llm | parser
"""
LLM answer generator — uses Google Gemini API to generate cited answers.
"""
from backend.services.gemini_client import generate_text

PROMPT_TEMPLATE = """You are an internal knowledge base assistant.
Answer the question ONLY using the context provided below.
If the context does not contain enough information to answer, say "I don't have enough information to answer this question based on the available documents."

Include citations like [1], [2] referring to the numbered sources below.
Use standard Markdown for lists and **bold** emphasis; place citation markers after each claim (e.g. **$29/user** [1]).
Be concise but thorough. Use bullet points or tables where appropriate.

Question: {question}

Sources:
{context}

Answer:"""


def generate_answer(question: str, ranked_chunks: list[dict]) -> dict:
    """
    Generate an AI answer using Gemini, grounded in the ranked chunks.

    Args:
        question: The user's question.
        ranked_chunks: Top chunks from search+rerank.

    Returns:
        Dict with 'answer' text and 'citations' list.
    """
    if not ranked_chunks:
        return {
            "answer": "I couldn't find any relevant documents to answer your question.",
            "citations": [],
        }

    # Build numbered context
    context_lines = []
    for i, chunk in enumerate(ranked_chunks, start=1):
        title = chunk.get("doc_title", "Unknown")
        dept = chunk.get("department", "")
        text = chunk["text"][:600]  # truncate long chunks
        context_lines.append(f"[{i}] ({title} — {dept} dept): {text}")

    prompt = PROMPT_TEMPLATE.format(
        question=question,
        context="\n\n".join(context_lines),
    )

    try:
        answer_text = generate_text(prompt)
    except Exception as e:
        error_msg = str(e)
        print(f"  ⚠ Gemini API error (all keys): {error_msg[:300]}")
        answer_text = _fallback_answer_text(question, ranked_chunks, error_msg)

    citations = parse_citations(answer_text, ranked_chunks)

    return {
        "answer": answer_text,
        "citations": citations,
    }


def _chunk_to_citation(marker: int, chunk: dict) -> dict:
    return {
        "marker": marker,
        "doc_title": chunk.get("doc_title", "Unknown"),
        "doc_id": chunk.get("doc_id", ""),
        "department": chunk.get("department", ""),
        "chunk_text": chunk["text"][:2500],
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "file_type": chunk.get("file_type", "markdown"),
    }


def _fallback_citations(chunks: list[dict], max_sources: int = 5) -> list[dict]:
    """Build citations from top chunks when the answer has no [N] markers."""
    import re

    citations = []
    seen_keys = set()
    marker = 1
    for chunk in chunks:
        title = (chunk.get("doc_title") or "").strip()
        key = re.sub(r"\s*\(PDF\)\s*$", "", title, flags=re.IGNORECASE).lower()
        if not key:
            key = chunk.get("doc_id", str(marker))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        citations.append(_chunk_to_citation(marker, chunk))
        marker += 1
        if marker > max_sources:
            break
    return citations


def _friendly_llm_notice(error_msg: str) -> str:
    """User-facing note when Gemini fails (no raw API payloads)."""
    low = (error_msg or "").lower()
    if "503" in error_msg or "high demand" in low or "unavailable" in low:
        return (
            "The AI service is busy right now. Try again in a minute — "
            "the citations below are still from your documents."
        )
    if "429" in error_msg or "quota" in low or "rate" in low:
        return (
            "API quota limit was reached. The citations below are from search results."
        )
    return (
        "Could not generate an AI summary. The citations below are from search results."
    )


def _fallback_answer_text(question: str, chunks: list[dict], error_msg: str) -> str:
    """Readable answer when Gemini is unavailable, with [1]…[N] markers."""
    notice = _friendly_llm_notice(error_msg)
    citations = _fallback_citations(chunks, max_sources=3)
    if not citations:
        return (
            f"[LLM unavailable — showing search results only]\n\n"
            f"I found relevant passages but couldn't generate an AI summary.\n\n"
            f"_{notice}_"
        )

    lines = [
        "[LLM unavailable — showing top search results with citations]\n",
        f"_{notice}_\n",
        f"Question: {question}\n",
        "Relevant excerpts:\n",
    ]
    for c in citations:
        chunk = chunks[c["marker"] - 1]
        snippet = chunk["text"][:400].strip().replace("\n", " ")
        lines.append(f"- **{c['doc_title']}** [{c['marker']}]: {snippet}…\n")
    return "\n".join(lines)


def parse_citations(answer: str, chunks: list[dict]) -> list[dict]:
    """
    Extract [N] citation markers from the answer and map to source chunks.
    """
    import re
    markers = set(int(m) for m in re.findall(r"\[(\d+)\]", answer))

    citations = []
    for marker in sorted(markers):
        idx = marker - 1  # convert 1-indexed to 0-indexed
        if 0 <= idx < len(chunks):
            citations.append(_chunk_to_citation(marker, chunks[idx]))

    if not citations and chunks:
        citations = _fallback_citations(chunks)

    return citations

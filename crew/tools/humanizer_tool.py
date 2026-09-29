"""Anti-AI Humanization & Perplexity Disruption Engine.

Transforms AI-generated synthesis drafts into authentic, publication-grade human writing
with high burstiness, high perplexity, and 0% AI detection probability.
"""

import re
import os
import math
from typing import List, Dict, Tuple, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# AI Signature Clichés and N-grams banned from final publication dossiers
BANNED_AI_PATTERNS = [
    (r"\bdelving\s+into\b", "examining"),
    (r"\bdelved\s+into\b", "examined"),
    (r"\bdelves\s+into\b", "examines"),
    (r"\bdelve\s+into\b", "examine"),
    (r"\ba\s+testament\s+to\b", "evidence of"),
    (r"\bpivotal\s+role\b", "key role"),
    (r"\bpivotal\b", "key"),
    (r"\bcrucial\s+to\s+note(?:\s+that)?\b", "notably"),
    (r"\bit\s+is\s+important\s+to\s+note(?:\s+that)?\b", ""),
    (r"\bit\s+is\s+worth\s+noting(?:\s+that)?\b", ""),
    (r"\bit\s+should\s+be\s+noted(?:\s+that)?\b", ""),
    (r"\bin\s+conclusion\b", "Ultimately"),
    (r"\bin\s+summary\b", "Ultimately"),
    (r"\bfurthermore\b", "Also"),
    (r"\bmoreover\b", "Beyond this"),
    (r"\bmultifaceted\b", "complex"),
    (r"\btapestry\s+of\b", "system of"),
    (r"\btapestry\b", "structure"),
    (r"\bbeacon\s+of\b", "benchmark for"),
    (r"\bbeacon\b", "guide"),
    (r"\bseamlessly\b", "smoothly"),
    (r"\bseamless\b", "smooth"),
    (r"\bintricate\s+dance\b", "interaction"),
    (r"\bgame-changer\b", "major shift"),
    (r"\blikewise\b", "similarly"),
    (r"\bholistic\s+approach\b", "integrated approach"),
    (r"\bunderscoring\s+the\s+importance\s+of\b", "highlighting"),
    (r"\bunderscoring\b", "highlighting"),
    (r"\bunderscores\b", "highlights"),
    (r"\bfosters\s+an\s+environment\s+of\b", "enables"),
    (r"\bfosters\s+an\s+environment\s+for\b", "enables"),
    (r"\bfosters\b", "supports"),
    (r"\brealm\s+of\b", "field of"),
]


def clean_ai_cliches(text: str) -> str:
    """Strip or replace signature LLM n-grams and formulaic filler."""
    cleaned = text
    for pattern, replacement in BANNED_AI_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    # Clean up any resulting double spaces
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex boundary detection."""
    # Strip markdown headers and tables for sentence metrics
    lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("#") and not line.startswith("|")]
    clean_text = " ".join(lines)
    if not clean_text:
        return []
    # Sentence boundary split
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"])", clean_text)
    return [s.strip() for s in sentences if len(s.strip().split()) > 2]


def calculate_burstiness(text: str) -> float:
    """Calculate the burstiness coefficient (standard deviation / mean sentence length).
    
    Human writing typically scores > 0.55 (erratic cadence).
    AI writing typically scores < 0.35 (monotonous cadence).
    """
    sentences = split_into_sentences(text)
    if len(sentences) < 2:
        return 0.0

    lengths = [len(s.split()) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    if mean_len == 0:
        return 0.0

    variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    return round(std_dev / mean_len, 3)


def chunk_markdown(content: str, max_chunk_chars: int = 3500) -> List[Dict[str, str]]:
    """Split markdown document into logical section chunks preserving headers."""
    sections = re.split(r"(?=\n##+\s)", content)
    chunks = []

    current_chunk = ""
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if len(current_chunk) + len(sec) < max_chunk_chars:
            current_chunk += ("\n\n" + sec if current_chunk else sec)
        else:
            if current_chunk:
                chunks.append({"text": current_chunk})
            current_chunk = sec

    if current_chunk:
        chunks.append({"text": current_chunk})

    return chunks if chunks else [{"text": content}]


HUMANIZER_SYSTEM_PROMPT = """You are a World-Class Principal Engineer, Chief Editor, and Technical Stylist.
Your sole mission is to rewrite the provided research section so it achieves ABSOLUTE 0% AI DETECTION across Turnitin, GPTZero, CopyLeaks, and Originality.ai.

STRICT ANTI-AI RULES:
1. CADENCE & BURSTINESS (CRITICAL):
   - Radically vary sentence lengths. Alternate between short, punchy 3–7 word sentences and intricate 30–45 word analytical clauses.
   - Break all robotic tripartite symmetry ("X, Y, and Z").
   - Use natural parentheticals, em-dashes (—), and semicolons.

2. VOCABULARY & TONE:
   - Write with the authoritative, pragmatic voice of an expert who builds real production systems.
   - BANNED WORDS: NEVER use 'delve', 'tapestry', 'testament', 'beacon', 'crucial', 'pivotal', 'game-changer', 'multifaceted', 'furthermore', 'moreover', 'in conclusion', 'seamless', 'realm', 'underscores'.
   - Use pragmatic transitions: "In production, however...", "The primary failure mode originates in...", "Under benchmark load...", "Practically speaking...".

3. FACT & CITATION PRESERVATION:
   - Preserve all technical facts, metrics, numbers, CVEs, benchmark stats, tables, and bracketed citation numbers ([1], [2]).
   - Retain standard Markdown headers (##, ###) and table formatting.

Output ONLY the rewritten markdown text. Do not include meta-commentary, introductory notes, or disclaimers."""


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1.5, min=2, max=10),
    reraise=True,
)
def rewrite_chunk_groq(chunk_text: str, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile") -> str:
    """Call Groq API with exponential backoff and rate-limit safety."""
    import requests

    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return clean_ai_cliches(chunk_text)

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": HUMANIZER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Rewrite the following research section to be completely human and undetectable:\n\n{chunk_text}"},
        ],
        "temperature": 0.65,
        "max_tokens": 4096,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=40,
        )
        if response.status_code == 429:
            # Fallback to faster, lower-rate-limit 8b model if 70b is heavily loaded
            if "70b" in model:
                return rewrite_chunk_groq(chunk_text, api_key=key, model="llama-3.1-8b-instant")
            response.raise_for_status()

        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()
        return clean_ai_cliches(result)
    except Exception as e:
        # Fallback to lighter model or cliché cleaner if network fails
        if "70b" in model:
            return rewrite_chunk_groq(chunk_text, api_key=key, model="llama-3.1-8b-instant")
        raise e


def humanize_research_dossier(markdown_text: str, api_key: Optional[str] = None) -> str:
    """End-to-end humanization pipeline for complete research reports."""
    if not markdown_text or len(markdown_text.strip()) < 50:
        return markdown_text

    chunks = chunk_markdown(markdown_text)
    humanized_sections = []

    for chunk in chunks:
        try:
            rewritten = rewrite_chunk_groq(chunk["text"], api_key=api_key)
            humanized_sections.append(rewritten)
        except Exception:
            # Safe fallback if completely disconnected
            humanized_sections.append(clean_ai_cliches(chunk["text"]))

    final_report = "\n\n".join(humanized_sections)
    return clean_ai_cliches(final_report)

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
    (r"\brapidly\s+evolving(?:\s+technological)?\s+landscape\b", "production environment"),
    (r"\btechnological\s+landscape\b", "systems ecosystem"),
    (r"\blandscape\b", "domain"),
    (r"\bdelving\s+into\b", "examining"),
    (r"\bdelved\s+into\b", "examined"),
    (r"\bdelves\s+into\b", "examines"),
    (r"\bdelve\s+into\b", "examine"),
    (r"\bdelve\b", "look"),
    (r"\ba\s+testament\s+to\b", "evidence of"),
    (r"\btestament\b", "evidence"),
    (r"\bpivotal\s+role\b", "key role"),
    (r"\bpivotal\b", "key"),
    (r"\bcrucial\s+to\s+note(?:\s+that)?\b", "notably"),
    (r"\bcrucial\b", "critical"),
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
    (r"\bparadigm\s+shift\b", "architectural transition"),
    (r"\blikewise\b", "similarly"),
    (r"\bholistic\s+approach\b", "integrated approach"),
    (r"\bholistic\b", "unified"),
    (r"\bunderscoring\s+the\s+importance\s+of\b", "highlighting"),
    (r"\bunderscoring\b", "highlighting"),
    (r"\bunderscores\b", "highlights"),
    (r"\bfosters\s+an\s+environment\s+of\b", "enables"),
    (r"\bfosters\s+an\s+environment\s+for\b", "enables"),
    (r"\bfosters\b", "supports"),
    (r"\brealm\s+of\b", "field of"),
    (r"\brealm\b", "field"),
    (r"\bTakeaway\s*:\s*", ""),
    (r"\bTakeaways\s*:\s*", ""),
    (r"\bKey\s+Takeaway\s*:\s*", ""),
]


def clean_ai_cliches(text: str) -> str:
    """Strip or replace signature LLM n-grams, formulaic filler, and repetitive AI wrappers."""
    cleaned = text
    for pattern, replacement in BANNED_AI_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    # Clean up empty list headers, leftover bullet cards, or double spaces
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex boundary detection."""
    lines = [line.strip() for line in text.split("\n") if line.strip() and not line.startswith("#") and not line.startswith("|")]
    clean_text = " ".join(lines)
    if not clean_text:
        return []
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


HUMANIZER_SYSTEM_PROMPT = """You are a Veteran Principal Systems Architect, Chief Security Researcher, and Technical Stylist.
Your sole mission is to rewrite the provided research draft so it is 100% INDISTINGUISHABLE FROM A TOP-TIER HUMAN RESEARCH PAPER and achieves 0% AI DETECTION across Turnitin, GPTZero, CopyLeaks, and Originality.ai.

CRITICAL ANTI-AI DIRECTIVES:
1. NATURAL HUMAN PROSE & STRUCTURE (CRITICAL):
   - DO NOT use repetitive, formulaic bullet cards (e.g. '• Point 1 • Success rate: ... • Citation: [X]'). Instead, weave findings into deep, authoritative paragraphs with natural inline citations [1], [2].
   - DO NOT include robotic 'Takeaway:' or 'Key Takeaway:' summary labels.
   - Alternate between dense, multi-clause analytical explanations (35–45 words) and sharp, definitive observations (4–8 words).

2. VOCABULARY PURGE:
   - NEVER use AI markers: 'delve', 'tapestry', 'testament', 'beacon', 'crucial', 'pivotal', 'game-changer', 'multifaceted', 'furthermore', 'moreover', 'in conclusion', 'seamless', 'realm', 'underscores', 'landscape', 'paradigm shift', 'holistic'.
   - Use pragmatic, first-principles transitions: "In real-world testing, however...", "The core failure mode stems from...", "Under benchmark stress...", "Practically speaking...".

3. FACTUAL & CITATION ACCURACY:
   - Retain every single technical fact, memory offset, CVE number, benchmark metric, and bracketed citation ([1], [2], etc.).
   - Preserve valid Markdown tables and section headers (##, ###).

Output ONLY the finalized, natural markdown report text."""


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

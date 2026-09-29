# Issue #18 Implementation Plan: Absolute 0% AI Detection Pipeline

## 1. Core Philosophy & Strategy
Achieving a true **0% AI detection score** (across Turnitin, Originality, GPTZero, etc.) requires addressing the two core metrics that all AI detectors analyze:
1. **Perplexity:** How predictable the next word is. (AI generates low perplexity; Humans generate high perplexity).
2. **Burstiness:** The variation in sentence rhythm and length. (AI generates uniform, robotic sentence lengths; Humans generate erratic, "bursty" sentences).

We will achieve this without arbitrary toggles. The pipeline will exclusively generate human-grade, undetectable text by enforcing extreme burstiness, banning specific predictable n-grams, and running text through a dedicated "Humanizer / Obfuscation" post-processing layer.

---

## 2. Pipeline Architecture & The "Humanizer Node"
Currently, the `Research Writer` outputs the final text. We will insert a **Dedicated Humanizer Agent/Layer** immediately after the Writer, but before the final markdown export.

**The Flow:**
`Evidence Analyst` -> `Research Writer (Draft)` -> **`Humanizer / Perplexity Injector (Final Polish)`** -> `Streamlit UI`

### Humanizer Layer Responsibilities:
- **Structural Disruption:** Splits symmetric paragraphs. Forces the inclusion of very short sentences (3-5 words) alongside very long, complex clauses (35+ words).
- **Cliché Stripper:** Uses a hardcoded RegEx ban list to strip and replace AI-specific transition words (e.g., *delve, testament, pivotal, crucial, tapestry, moreover, in conclusion*).
- **Typographic Authenticators:** Injects authentic human typography patterns (em-dashes, semicolons, parenthetical asides) which LLMs rarely use naturally.

---

## 3. Groq API Limits & Robustness (Bulletproofing)
Because generating high-perplexity text requires high temperatures and multiple passes, and Groq has strict free-tier rate limits (Requests Per Minute / Tokens Per Minute), the pipeline must be **bulletproof**:

1. **Chunked Processing:** The Humanizer will not process a 3,000-word report in one API call. It will chunk the report by section headers (`##`) and process them asynchronously or sequentially.
2. **Exponential Backoff:** We will integrate the `tenacity` library in the humanizer tool/agent to automatically catch `429 Too Many Requests` or `503 Service Unavailable` errors from Groq, wait, and retry without crashing the Streamlit app.
3. **Fallback Models:** If `llama3-70b-8192` hits rate limits, the tool will gracefully downgrade to `llama3-8b-8192` for specific chunks.

---

## 4. The "Zero Percent" Prompt Engineering

We will inject a system prompt payload directly into the Humanizer Agent. 

**Example Directives to be Implemented:**
* *"You are an abrasive, highly opinionated Principal Engineer. Rewrite the following text to sound like it was written by a human expert in a raw, direct style."*
* *"CRITICAL RULES: Vary sentence length drastically. Write one sentence that is 40 words long and complex. Follow it immediately with a 4-word sentence. Never use tripartite lists (X, Y, and Z)."*
* *"BANNED WORDS: delve, realm, landscape, moreover, crucial, pivotal, multifaceted, testament. If you use these words, the build will fail."*

---

## 5. Harsh Testing & User Flow QA
We cannot guess if the text is undetectable; we must test it mathematically during CI/CD.

### A. Local Perplexity & Burstiness Testing
We will add a new test file `scripts/test_ai_detection.py`. It will:
- Use `nltk` to calculate sentence length standard deviation (Burstiness). The test will **fail** if the burstiness score is below `0.5`.
- Calculate word-choice variance to approximate perplexity.

### B. Streamlit User Flow Testing
- Ensure the UI handles the extra ~15-30 seconds required by the Humanizer layer. 
- Implement a distinct progress spinner in Streamlit: `st.spinner("Applying humanization and anti-AI obfuscation layer...")` so the user knows why the app is thinking.

---

## 6. Execution Steps (Using Gemini Models)

When you are ready to begin, we will execute the following phases atomically:

1. **Phase A:** Update `requirements.txt` to include `tenacity` (for Groq resilience) and `nltk` (for local burstiness testing).
2. **Phase B:** Create `crew/tools/humanizer_tool.py` and `crew/agents/humanizer.py` with the 0% detection system prompts and chunking logic.
3. **Phase C:** Wire the new agent into `crew/crew.py` directly after the Research Writer.
4. **Phase D:** Add the `tenacity` retry wrappers around the Groq LLM calls.
5. **Phase E:** Build the testing script and test the pipeline end-to-end to verify burstiness mathematically.

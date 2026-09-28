"""Interactive Research Dossier Editor & Chat Agent.

Enables ChatGPT-like multi-turn conversations and surgical, token-efficient
editing/expansion of research dossiers without token truncation.
"""

import re
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Tuple, List, Dict


def extract_dossier_outline(markdown_text: str) -> str:
    """Extract a clean markdown outline (headings hierarchy) of the dossier."""
    headings = []
    for line in markdown_text.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("#"):
            headings.append(trimmed)
    if not headings:
        return "(No structured headings found)"
    return "\n".join(headings)


def apply_section_edit(
    current_dossier: str,
    action: str,
    target_heading: str,
    new_content: str
) -> str:
    """Surgically apply an edit, insertion, or replacement to a Markdown dossier.
    
    Actions:
        - INSERT_AFTER: Insert new_content after the target section (before next heading of same or higher level)
        - INSERT_BEFORE: Insert new_content before the target heading
        - REPLACE_SECTION: Replace the target section with new_content
        - APPEND_END: Append new_content to the end of the dossier
        - PREPEND_START: Insert new_content right after the main title (H1)
        - FULL_UPDATE: Replace entire dossier with new_content
    """
    if not current_dossier.strip():
        return new_content.strip()

    action = (action or "APPEND_END").strip().upper()
    new_content = new_content.strip()
    target_heading = (target_heading or "").strip()

    if action == "FULL_UPDATE":
        return new_content

    if action == "APPEND_END" or not target_heading:
        return f"{current_dossier.rstrip()}\n\n{new_content}\n"

    # Normalize target heading search string
    target_clean = re.sub(r"^[#\s]+", "", target_heading).strip().lower()
    
    lines = current_dossier.splitlines()
    target_line_idx = -1
    target_level = 1

    # Find the line matching target heading
    for idx, line in enumerate(lines):
        trimmed = line.strip()
        if trimmed.startswith("#"):
            heading_text = re.sub(r"^[#\s]+", "", trimmed).strip().lower()
            # Match if target_clean is in heading or vice versa
            if target_clean in heading_text or heading_text in target_clean:
                target_line_idx = idx
                # Count the # level
                match = re.match(r"^(#+)", trimmed)
                target_level = len(match.group(1)) if match else 2
                break

    if target_line_idx == -1:
        # Fallback: if heading not found by fuzzy match, append to end
        return f"{current_dossier.rstrip()}\n\n{new_content}\n"

    # Find the end of this section (the next heading of same or higher level, or EOF)
    next_section_idx = len(lines)
    for idx in range(target_line_idx + 1, len(lines)):
        trimmed = lines[idx].strip()
        if trimmed.startswith("#"):
            match = re.match(r"^(#+)", trimmed)
            level = len(match.group(1)) if match else 2
            if level <= target_level:
                next_section_idx = idx
                break

    if action == "INSERT_AFTER":
        # Insert before next section
        before = lines[:next_section_idx]
        after = lines[next_section_idx:]
        updated_lines = before + ["", new_content, ""] + after
        return "\n".join(updated_lines).strip() + "\n"

    elif action == "INSERT_BEFORE":
        # Insert right before the target heading
        before = lines[:target_line_idx]
        after = lines[target_line_idx:]
        updated_lines = before + ["", new_content, ""] + after
        return "\n".join(updated_lines).strip() + "\n"

    elif action == "REPLACE_SECTION":
        # Replace from target_line_idx up to next_section_idx
        before = lines[:target_line_idx]
        after = lines[next_section_idx:]
        updated_lines = before + ["", new_content, ""] + after
        return "\n".join(updated_lines).strip() + "\n"

    elif action == "PREPEND_START":
        # Find H1 if exists
        h1_idx = 0
        for idx, line in enumerate(lines):
            if line.strip().startswith("# "):
                h1_idx = idx + 1
                break
        before = lines[:h1_idx]
        after = lines[h1_idx:]
        updated_lines = before + ["", new_content, ""] + after
        return "\n".join(updated_lines).strip() + "\n"

    return f"{current_dossier.rstrip()}\n\n{new_content}\n"


def execute_llm_call(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    max_retries: int = 8,
    model_name: str = "openai/gpt-oss-120b"
) -> str:
    """Robust Groq API caller with multi-model fallback, dynamic rate-limit backoff, and token management."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    models_cascade = [model_name, "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    
    payload = {
        "model": models_cascade[0],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            last_error = e
            err_text = ""
            try:
                err_text = e.read().decode("utf-8")
            except Exception:
                pass

            if e.code == 429:
                wait_sec = None
                if "Retry-After" in e.headers:
                    try:
                        wait_sec = float(e.headers.get("Retry-After")) + 1.0
                    except Exception:
                        pass
                if not wait_sec and err_text:
                    m = re.search(r"try again in (\d+\.?\d*)s", err_text, re.IGNORECASE)
                    if m:
                        wait_sec = float(m.group(1)) + 1.0

                if not wait_sec:
                    wait_sec = [3, 6, 12, 20, 30, 45, 60, 60][min(attempt, 7)]

                if attempt >= 1 and len(models_cascade) > 1:
                    next_model = models_cascade[min(attempt, len(models_cascade) - 1)]
                    payload["model"] = next_model

                time.sleep(wait_sec)

            elif e.code == 413:
                # If prompt is too large, trim middle of context while keeping instructions
                user_msg = payload["messages"][1]["content"]
                if len(user_msg) > 12000:
                    payload["messages"][1]["content"] = user_msg[:4000] + "\n\n[...context omitted for brevity...]\n\n" + user_msg[-6000:]
                time.sleep(2)
            else:
                if attempt < max_retries - 1:
                    time.sleep(3)
                else:
                    raise e
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                raise e

    if last_error:
        raise last_error
    raise RuntimeError("Failed to complete LLM request after retries.")


def handle_follow_up_chat(
    user_query: str,
    current_report: str,
    api_key: str,
    session_id: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """Handle ChatGPT-like conversation and intelligent dossier modifications.
    
    Returns:
        tuple (reply_message, updated_report_or_none)
    """
    outline = extract_dossier_outline(current_report)
    
    # Provide relevant context snippet to avoid overflowing context window
    dossier_context = current_report
    if len(current_report) > 25000:
        # Include first 10k chars and last 10k chars
        dossier_context = (
            current_report[:12000]
            + f"\n\n... [Full dossier is ~{len(current_report)} chars. Outline above shows all sections] ...\n\n"
            + current_report[-12000:]
        )

    system_prompt = (
        "Role: Senior Research Editor & Multi-Agent Lead\n"
        "Goal: You are the interactive AI researcher and editor for an active research dossier.\n\n"
        "Instructions:\n"
        "1. If the user asks a QUESTION, CLARIFICATION, or DISCUSSION (e.g., 'What is Kyber?', 'Explain side channels'):\n"
        "   - Provide an insightful, deep, citation-backed conversational answer.\n"
        "   - Do NOT include any edit markers or delimiters.\n\n"
        "2. If the user asks to ADD, EDIT, EXPAND, or REWRITE the dossier (e.g., 'Add a subsection in Part 2 titled...', 'Rewrite Section 3', 'Update conclusion'):\n"
        "   - First, write a clear, polite summary in your response explaining exactly what was updated or added.\n"
        "   - Then, provide the surgical edit instructions using the exact format below:\n\n"
        "<<<EDIT_ACTION>>>\n"
        "ACTION: [INSERT_AFTER | INSERT_BEFORE | REPLACE_SECTION | APPEND_END | FULL_UPDATE]\n"
        "TARGET_HEADING: [The exact heading in the dossier to attach or modify, e.g., '## Part 2:' or '## Conclusion']\n"
        "NEW_CONTENT:\n"
        "[Complete Markdown content for the new or revised section, including headings, data tables, equations, and citations]\n"
        "<<<END_EDIT>>>\n\n"
        "Maintain absolute academic rigor, exact technical specifications, and clean Markdown formatting."
    )

    user_prompt = (
        f"USER DIRECTIVE / INQUIRY:\n"
        f"\"{user_query}\"\n\n"
        f"--- ACTIVE DOSSIER OUTLINE ---\n"
        f"{outline}\n\n"
        f"--- ACTIVE DOSSIER CONTENT ---\n"
        f"{dossier_context}"
    )

    response = execute_llm_call(system_prompt, user_prompt, api_key, temperature=0.2, max_tokens=4096)

    # Check for surgical edit action
    if "<<<EDIT_ACTION>>>" in response:
        parts = response.split("<<<EDIT_ACTION>>>")
        reply_msg = parts[0].strip()
        edit_block = parts[1]
        if "<<<END_EDIT>>>" in edit_block:
            edit_block = edit_block.split("<<<END_EDIT>>>")[0]

        # Parse action, target_heading, and new_content
        action_match = re.search(r"ACTION:\s*([A-Z_]+)", edit_block)
        action = action_match.group(1).strip() if action_match else "INSERT_AFTER"

        heading_match = re.search(r"TARGET_HEADING:\s*([^\n]+)", edit_block)
        target_heading = heading_match.group(1).strip() if heading_match else ""

        content_match = re.search(r"NEW_CONTENT:\s*\n(.*)", edit_block, re.DOTALL)
        new_content = content_match.group(1).strip() if content_match else edit_block.strip()

        # Apply the edit to the full current_report
        updated_dossier = apply_section_edit(current_report, action, target_heading, new_content)
        return reply_msg, updated_dossier

    # Check legacy full update delimiter
    elif "<<<UPDATED_DOSSIER>>>" in response:
        parts = response.split("<<<UPDATED_DOSSIER>>>")
        reply_msg = parts[0].strip()
        updated_report = parts[1].strip()
        return reply_msg, updated_report

    else:
        return response.strip(), None

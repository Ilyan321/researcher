"""Minimal LLM smoke test for CrewAI + Groq openai/gpt-oss-120b."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import get_llm, get_groq_api_key, DEFAULT_MODEL


def run_smoke_test():
    """Build the smallest valid single-agent configuration."""
    print(f"Testing LLM configuration for model: {DEFAULT_MODEL}")
    
    api_key = get_groq_api_key()
    if not api_key:
        print("Note: GROQ_API_KEY not set in environment or Streamlit secrets.")
        print("Static configuration and agent instantiation check will proceed.")

    try:
        from crewai import Agent, Task, Crew

        # 1. Initialize LLM
        llm = get_llm()
        print("✓ Successfully configured LLM instance via config.get_llm()")

        # 2. Build minimal single agent
        smoke_agent = Agent(
            role="Smoke Tester",
            goal="Verify LLM connectivity and configuration with Groq gpt-oss-120b",
            backstory="A lightweight verification agent ensuring the LLM pipeline is operational.",
            llm=llm,
            verbose=False,
        )
        print("✓ Successfully initialized single test Agent")

        # 3. Build minimal task
        smoke_task = Task(
            description="Respond with 'LLM connection operational' if you can read this.",
            expected_output="A short confirmation message.",
            agent=smoke_agent,
        )
        print("✓ Successfully initialized test Task")

        # 4. Construct Crew
        crew = Crew(
            agents=[smoke_agent],
            tasks=[smoke_task],
            verbose=False,
        )
        print("✓ Successfully assembled minimal single-agent Crew")

        # 5. If live API key is provided, attempt kickoff
        if api_key:
            print("Attempting live kickoff with Groq...")
            result = crew.kickoff()
            print(f"✓ Live response received: {result}")
        else:
            print("✓ Smoke test passed: Configuration & object graph validated.")

        return True

    except Exception as e:
        print(f"✗ Smoke test failed with error: {e}")
        return False


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)

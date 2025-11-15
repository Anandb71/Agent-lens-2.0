import os
from google.genai import types
from google.adk.models.google_llm import Gemini
from google.adk.agents import Agent

# --- Common Retry Configuration ---
# Use HttpRetryOptions here
retry_config = types.HttpRetryOptions(
    attempts=5, exp_base=7, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)

# --- LLM for all agents ---
LLM = Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config)

# --- 1. The Buggy Agent (for the Client to run) ---
# NOTE: This agent is run *LOCALLY* by the client, but defined here for consistency.
def create_buggy_agent() -> Agent:
    """Creates the agent that is intentionally missing the Google Search tool."""
    return Agent(
        name="BuggyAgent",
        model=LLM,
        instruction="You are a helpful research assistant. You MUST use the `Google Search` tool to find information.",
        tools=[],
    )

# --- 2. The Debug Critic Agent ---
def create_debug_critic_agent() -> Agent:
    """The agent that analyzes a failed trace and identifies the root cause."""
    return Agent(
        name="DebugCriticAgent",
        model=LLM,
        instruction="""You are the Debug Critic. Your task is to analyze the provided agent trace (Agent Prompt and Trace JSON)
        and determine the single, specific root cause of the agent's failure.
        Your output MUST be a concise, professional critique that clearly identifies the error (e.g., 'Agent was asked to use tool X but did not have it.', 'Agent entered an infinite loop due to ambiguous instructions.').""",
        tools=[],
    )

# --- 3. The Prompt Refiner Agent ---
def create_prompt_refiner_agent() -> Agent:
    """The agent that suggests a fix based on the critic's analysis."""
    return Agent(
        name="PromptRefinerAgent",
        model=LLM,
        instruction="""You are the Prompt Refiner. Based on the provided original prompt and the Bug Critique,
        your task is to provide a detailed, actionable technical suggestion for the developer to fix the agent's code or prompt.
        Your output MUST be focused on technical implementation details, such as missing tool imports, clearer instruction phrasing, or necessary code logic.
        Include example Python code if a tool is missing.""",
        tools=[],
    )
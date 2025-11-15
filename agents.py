import asyncio
import os
import logging
import json
import uuid
from google.genai import types
from google.adk.agents import Agent, LlmAgent  # LoopAgent and FunctionTool are removed
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session

# --- 1. Set up Logging and API Key ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AGENT_LENS_2.0")

try:
    if "GOOGLE_API_KEY" not in os.environ:
        logger.error("🔑 Authentication Error: GOOGLE_API_KEY environment variable not set. Exiting.")
        logger.error("Please set the variable in your terminal before running.")
        exit()
    
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    logger.info("✅ Gemini API key setup complete.")
except Exception as e:
    logger.error(f"🔑 An unexpected error occurred during setup: {e}")
    exit()

retry_config = types.HttpRetryOptions(
    attempts=5, exp_base=7, initial_delay=1, http_status_codes=[429, 500, 503, 504]
)

# --- 2. Define The "Buggy" Agent We Want to Debug ---
buggy_agent = Agent(
    name="BuggyAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="You are a helpful research assistant. You MUST use the `Google Search` tool to find information.",
    tools=[],
)
logger.info("✅ BuggyAgent created.")


# --- 3. Define The "Debug & Refine" Agents (Our Meta-Agents) ---

# The Critic agent now just needs to return its analysis.
# We remove the output_key and let it return the text directly.
debug_critic_agent = Agent(
    name="DebugCriticAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an expert AI Agent Debugger. You will be given the original prompt and the full execution trace (in JSON) of a failed agent.
    Your task is to find the *root cause* of the failure.

    Analyze the trace step-by-step.
    1. Look at the `parts` with `function_call`.
    2. Look at the `parts` with `function_response`.
    3. Look at the final `text` response from the agent.
    4. Identify the *exact* reason for the failure (e.g., "The agent tried to call `Google Search` but that tool was not in its `tools` list," or "The agent failed to parse the user's request.").
    
    Respond *only* with your final analysis.
    """,
    # output_key="bug_critique", # No longer needed, we will get the final text response
)
logger.info("✅ DebugCriticAgent created.")

# The Refiner agent no longer needs the 'APPROVED' logic or exit_loop tool.
prompt_refiner_agent = Agent(
    name="PromptRefinerAgent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an expert Prompt Engineer. You have an agent's original prompt and a bug critique.
    Your task is to fix the bug by rewriting the agent's prompt or instructions.

    Provide the new, corrected agent prompt. Do not explain your changes, just provide the new prompt text.
    """,
    # output_key="suggested_fix", # No longer needed
    # tools=[], # No longer needs exit_loop
)
logger.info("✅ PromptRefinerAgent created.")

# --- LoopAgent and exit_loop() are GONE ---

# --- 4. Define the Main Execution Function (with fixes) ---
async def main():
    """
    Main function to orchestrate the "Observe -> Evolve" loop.
    """
    if "GOOGLE_API_KEY" not in os.environ:
        logger.error("🔴 GOOGLE_API_KEY not set. Exiting.")
        return
    
    app_name = "AgentLensDebugger" # Define app_name once

    # --- PART 1: "OBSERVE" (Run the buggy agent and capture its trace) ---
    logger.info("--- 🚀 [Step 1: OBSERVE] Running the BuggyAgent... ---")
    
    buggy_runner = InMemoryRunner(agent=buggy_agent, app_name=app_name) 
    buggy_prompt = "What is the latest news on quantum computing?"
    buggy_trace_events = []
    buggy_final_response = ""
    
    try:
        # run_debug returns the list of events, let's capture it
        events = await buggy_runner.run_debug(buggy_prompt)
        buggy_trace_events = events
        # The last event is the final response
        if events and events[-1].content and events[-1].content.parts:
            buggy_final_response = events[-1].content.parts[0].text
        logger.info("[OBSERVE] BuggyAgent ran without crashing.")
    except Exception as e:
        logger.warning(f"[OBSERVE] BuggyAgent failed as expected: {e}")
        # Use get_trace() instead of get_events()
        buggy_trace_events = buggy_runner.get_trace()

    # --- Use .model_dump(mode='json') instead of .to_dict() ---
    trace_json = json.dumps(
        [event.model_dump(mode='json') for event in buggy_trace_events], 
        indent=2
    )
    logger.info("--- 🏁 [Step 1: OBSERVE] Trace captured. ---")


    # --- PART 2: "EVOLVE" (Run the Debug Loop manually) ---
    logger.info("--- 🚀 [Step 2: EVOLVE] Starting the Manual Debug Loop... ---")

    # --- 2a. Run the Critic ---
    logger.info("--- 📞 Calling DebugCriticAgent... ---")
    
    # We must pass the prompt and trace *into* the prompt for the critic
    critic_prompt = f"""You are an expert AI Agent Debugger. You will be given the original prompt and the full execution trace (in JSON) of a failed agent.
    Your task is to find the *root cause* of the failure.

    - **Agent Prompt:** {buggy_agent.instruction}
    - **Failed Trace:** {trace_json}

    Analyze the trace step-by-step.
    1. Look at the `parts` with `function_call`.
    2. Look at the `parts` with `function_response`.
    3. Look at the final `text` response from the agent.
    4. Identify the *exact* reason for the failure (e.g., "The agent tried to call `Google Search` but that tool was not in its `tools` list," or "The agent failed to parse the user's request.").
    
    Respond *only* with your final analysis.
    """
    
    critic_runner = InMemoryRunner(agent=debug_critic_agent, app_name=app_name)
    critic_events = await critic_runner.run_debug(critic_prompt)
    bug_critique = critic_events[-1].content.parts[0].text
    
    logger.info(f"--- ✅ [CRITIC] Responded: {bug_critique[:50]}... ---")

    # --- 2b. Run the Refiner ---
    logger.info("--- 📞 Calling PromptRefinerAgent... ---")
    
    # We pass the prompt and the critique *into* the prompt for the refiner
    refiner_prompt = f"""You are an expert Prompt Engineer. You have an agent's original prompt and a bug critique.
    Your task is to fix the bug by rewriting the agent's prompt or instructions.

    - **Original Prompt:** {buggy_agent.instruction}
    - **Bug Critique:** {bug_critique}

    Provide the new, corrected agent prompt. Do not explain your changes, just provide the new prompt text.
    """
    
    refiner_runner = InMemoryRunner(agent=prompt_refiner_agent, app_name=app_name)
    refiner_events = await refiner_runner.run_debug(refiner_prompt)
    suggested_fix = refiner_events[-1].content.parts[0].text

    logger.info(f"--- ✅ [REFINER] Responded: {suggested_fix[:50]}... ---")
    logger.info("--- 🏁 [Step 2: EVOLVE] Manual Debug Loop Complete. ---")

    # --- PART 3: The Results ---
    print("\n\n" + "="*50)
    logger.info("🏆 AGENT LENS 2.0: DEBUGGING RESULTS 🏆")
    print("="*50)
    
    print("\n--- ORIGINAL BUGGY PROMPT ---")
    print(buggy_agent.instruction)

    print("\n--- BUGGY AGENT'S FINAL (FAILED) RESPONSE ---")
    print(buggy_final_response)
    
    print("\n--- [CRITIC] ROOT CAUSE ANALYSIS ---")
    print(bug_critique)
    
    print("\n--- [REFINER] SUGGESTED FIX ---")
    print(suggested_fix)
    print("\n" + "="*50)


if __name__ == "__main__":
    asyncio.run(main())
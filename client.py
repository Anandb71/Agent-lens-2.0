import asyncio
import os
import logging
import json

# --- ADK Imports ---
from google.genai import types
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
import httpx # NEW IMPORT

# --- 1. Set up Logging and API Key ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AGENT_LENS_2.0_CLIENT")

try:
    if "GOOGLE_API_KEY" not in os.environ:
        logger.error("🔑 Authentication Error: GOOGLE_API_KEY environment variable not set. Exiting.")
        logger.error("Please set the variable in your terminal before running.")
        exit()
    
    # The API key is needed here to run the "buggy_agent" locally
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    logger.info("✅ Gemini API key setup complete.")
except Exception as e:
    logger.error(f"🔑 An unexpected error occurred during setup: {e}")
    exit()

# Use the correct HttpRetryOptions
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

# --- 3. Define the Main Execution Function ---
async def main():
    """
    Main function to orchestrate the "Observe -> Evolve" loop
    by calling our remote REST API server.
    """
    if "GOOGLE_API_KEY" not in os.environ:
        logger.error("🔴 GOOGLE_API_KEY not set. Exiting.")
        return
    
    app_name = "AgentLensClient" # This is our client's app name
    SERVER_URL = "https://agent-lens-service-73526128850.us-central1.run.app"

    # --- PART 1: "OBSERVE" (Run the buggy agent and capture its trace) ---
    logger.info("--- 🚀 [Step 1: OBSERVE] Running the BuggyAgent... ---")
    
    buggy_runner = InMemoryRunner(agent=buggy_agent, app_name=app_name) 
    buggy_prompt = "What is the latest news on quantum computing?"
    buggy_trace_events = []
    
    try:
        events = await buggy_runner.run_debug(buggy_prompt)
        buggy_trace_events = events
        logger.info("[OBSERVE] BuggyAgent ran without crashing.")
    except Exception as e:
        logger.warning(f"[OBSERVE] BuggyAgent failed as expected: {e}")
        # Use get_trace() which exists on the runner
        buggy_trace_events = buggy_runner.get_trace()

    trace_json = json.dumps(
        [event.model_dump(mode='json') for event in buggy_trace_events], 
        indent=2
    )
    logger.info("--- 🏁 [Step 1: OBSERVE] Trace captured. ---")


    # --- PART 2: "CALL SERVICE" (Send trace to the REST API Service) ---
    logger.info(f"--- 📞 Calling AgentOps Service at {SERVER_URL}/debug ---")
    
    payload = {
        "agent_prompt": buggy_agent.instruction,
        "trace_json": trace_json
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{SERVER_URL}/debug", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info("--- 🏁 [Step 2: EVOLVE] REST API Response Received. ---")

            # --- PART 3: The Results ---
            print("\n\n" + "="*50)
            logger.info("🏆 AGENT LENS 2.0: DEBUGGING SERVICE RESPONSE 🏆")
            print("="*50)
            
            print("\n--- [CRITIC] ROOT CAUSE (from server) ---")
            print(result.get('critique', 'N/A'))
            
            print("\n--- [REFINER] SUGGESTED FIX (from server) ---")
            print(result.get('suggested_fix', 'N/A'))
            print("\n" + "="*50)

    except httpx.HTTPStatusError as e:
        logger.error(f"--- ❌ HTTP Error calling service: {e} ---")
        logger.error(f"Response detail: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"--- ❌ Request Error calling service: {e} ---")


if __name__ == "__main__":
    asyncio.run(main())
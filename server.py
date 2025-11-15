import asyncio
import os
import logging
import json
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager # NEW IMPORT

# --- ADK Imports ---
from google.genai import types
from google.adk.agents import Agent, LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool

# --- 1. Import Agents from our Library ---
try:
    from agents import debug_critic_agent, prompt_refiner_agent, retry_config
except ImportError:
    print("ERROR: Could not import from 'agents'. Make sure you have renamed 'agent.py' to 'agents.py'")
    exit()

# --- 2. Set up Logging and Constants ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AGENT_LENS_2.0_SERVER")

# --- FIX: Dynamic Database Path for Local vs. Cloud ---
# Cloud Run provides a PORT env var; local runs do not.
if os.environ.get('PORT'):
    # Running in Cloud Run (read-only filesystem)
    DATABASE_FILE = "/tmp/bug_database.json"
else:
    # Running locally
    DATABASE_FILE = "./bug_database.json"

APP_NAME = "AgentLensDebugger"
USER_ID = "service-user"

# Define the request body structure
class DebugRequest(BaseModel):
    agent_prompt: str
    trace_json: str

# --- Helper function for database initialization ---
def initialize_database():
    """Creates bug_database.json if it doesn't exist."""
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "w") as f:
            json.dump([], f)
        logger.info(f"--- 💾 Created empty database file: {DATABASE_FILE} ---")

# --- 3. Define The Core "Evolve" Logic as a Tool ---

async def run_debug_analysis(agent_prompt: str, trace_json: str) -> dict:
    """
    This is the core logic of our meta-agent. It runs the debug loop
    and saves the result to memory.
    """
    logger.info(f"--- 🚀 [Step 2: EVOLVE] Starting Debug Loop... ---")

    # --- 2a. Run the Critic ---
    logger.info("--- 📞 Calling DebugCriticAgent... ---")
    critic_prompt = f"""{debug_critic_agent.instruction}
    Here is the agent prompt and trace:
    - **Agent Prompt:** {agent_prompt}
    - **Failed Trace:** {trace_json}
    """
    
    critic_runner = InMemoryRunner(agent=debug_critic_agent, app_name=APP_NAME)
    critic_events = await critic_runner.run_debug(critic_prompt)
    bug_critique = critic_events[-1].content.parts[0].text
    logger.info(f"--- ✅ [CRITIC] Responded: {bug_critique[:50]}... ---")

    # --- 2b. Run the Refiner ---
    logger.info("--- 📞 Calling PromptRefinerAgent... ---")
    refiner_prompt = f"""{prompt_refiner_agent.instruction}
    Here is the prompt and critique:
    - **Original Prompt:** {agent_prompt}
    - **Bug Critique:** {bug_critique}
    """
    
    refiner_runner = InMemoryRunner(agent=prompt_refiner_agent, app_name=APP_NAME)
    refiner_events = await refiner_runner.run_debug(refiner_prompt)
    suggested_fix = refiner_events[-1].content.parts[0].text
    logger.info(f"--- ✅ [REFINER] Responded: {suggested_fix[:50]}... ---")

    # --- 2c. Implement Memory (Day 3 Concept) ---
    logger.info("--- 💾 Saving to Memory (bug_database.json)... ---")
    new_bug_report = {
        "bug_id": f"bug_{uuid.uuid4().hex[:8]}",
        "timestamp": asyncio.get_event_loop().time(),
        "original_prompt": agent_prompt,
        "critique": bug_critique,
        "suggested_fix": suggested_fix,
        "trace": json.loads(trace_json) # Store the trace as an object
    }
    
    try:
        # Use read/write with file locking for safety
        with open(DATABASE_FILE, "r+") as f:
            data = json.load(f)
            data.append(new_bug_report)
            f.seek(0)
            json.dump(data, f, indent=2)
        logger.info(f"--- ✅ Bug {new_bug_report['bug_id']} saved to memory. ---")
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"--- ❌ FAILED to save to memory: {e} ---")
        # Even if saving fails, return the result to the user
        return {"error": "Debug analysis complete, but failed to save to memory."}

    logger.info("--- 🏁 [Step 2: EVOLVE] Debug Loop Complete. ---")
    
    return {
        "critique": bug_critique,
        "suggested_fix": suggested_fix
    }

# --- 4. Define the FastAPI App and Manual Endpoint (Working Version) ---

# FIX: Use modern lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_database()
    yield
    # Shutdown (nothing needed here)

app = FastAPI(lifespan=lifespan)
logger.info("✅ FastAPI App created.")

# --- 5. Define the Agent Endpoint ---
@app.post("/debug")
async def debug_agent(request: DebugRequest):
    """
    Exposes our core logic as a network service.
    """
    try:
        result = await run_debug_analysis(request.agent_prompt, request.trace_json)
        return result
    except Exception as e:
        logger.error(f"--- ❌ Debug analysis failed: {e} ---")
        raise HTTPException(status_code=500, detail=str(e))

# --- 6. Add Bonus "Memory" Endpoint (from old server) ---
@app.get("/memory")
async def get_memory():
    """
    A simple FastAPI endpoint to read and display our bug database.
    This proves our memory is persistent.
    """
    logger.info("--- 📞 /memory endpoint called. ---")
    try:
        with open(DATABASE_FILE, "r") as f:
            data = json.load(f)
            return data
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"--- ❌ FAILED to read from memory: {e} ---")
        raise HTTPException(status_code=500, detail="Could not read bug database.")

# --- 7. Make the Server Runnable ---
if __name__ == "__main__":
    logger.info("🚀 Starting AGENT LENS 2.0 Server...")
    # We must run the server this way so it can handle async agent calls
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
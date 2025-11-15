import asyncio
import os
import logging
import json
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import InMemoryRunner
from contextlib import asynccontextmanager  # <-- Modern FastAPI context

# --- 1. Import Agent Creation Functions from our Library ---
# We now import *functions* to create agents, not the agents themselves.
try:
    from agents import create_debug_critic_agent, create_prompt_refiner_agent
except ImportError:
    print("ERROR: Could not import agent creation functions from 'agents'.")
    exit()

# --- 2. Set up Logging and Constants ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AGENT_LENS_2.0_SERVER")

# --- DATABASE PATH FIX ---
# Check if we are in the Google Cloud Run environment (which sets a PORT)
# If we are, use the /tmp directory (writeable). Otherwise, use the local directory.
if os.environ.get('PORT'):
    logger.info("Running in Cloud Run (Deployment) mode. Using /tmp for database.")
    DATABASE_FILE = "/tmp/bug_database.json"
else:
    logger.info("Running in Local (Development) mode. Using current directory for database.")
    DATABASE_FILE = "./bug_database.json"
# --- END FIX ---

APP_NAME = "AgentLensDebugger"
USER_ID = "service-user"

# --- 3. LAZY LOADING / SINGLETON CONTAINER ---
# This holds the initialized agents. It will only be populated when get_agent() is called.
AGENTS = {} 

def get_agent(agent_name: str):
    """Initializes and returns an agent instance (Lazy Loading/Singleton Pattern)."""
    if agent_name not in AGENTS:
        logger.info(f"Initializing {agent_name} for the first time...")
        if agent_name == "DebugCriticAgent":
            AGENTS[agent_name] = create_debug_critic_agent()
        elif agent_name == "PromptRefinerAgent":
            AGENTS[agent_name] = create_prompt_refiner_agent()
        else:
            raise ValueError(f"Unknown agent name: {agent_name}")
    return AGENTS[agent_name]


def initialize_database():
    """Creates the database file if it doesn't exist."""
    if not os.path.exists(DATABASE_FILE):
        logger.warning(f"Database file not found at {DATABASE_FILE}. Creating a new empty file.")
        try:
            # We must use a context manager to ensure file is closed, even on crash
            with open(DATABASE_FILE, "w") as f:
                json.dump([], f) # Write an empty list
            logger.info("Successfully created empty database file.")
        except IOError as e:
            logger.error(f"FATAL: Could not create database file: {e}")
            # The server will likely crash if the file system is read-only here

# --- 4. The Core "Evolve" Logic as a Tool ---

async def run_debug_analysis(agent_prompt: str, trace_json: str) -> dict:
    """
    This is the core logic of our meta-agent. It runs the debug loop
    and saves the result to memory.
    """
    # Retrieve agents from cache (they were created during lifespan startup)
    debug_critic_agent = get_agent("DebugCriticAgent")
    logger.info(f"--- 🚀 [Step 2: EVOLVE] Starting Manual Debug Loop... ---")

    # --- 2a. Run the Critic (Lazy Loaded) ---
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

    # --- 2b. Run the Refiner (Lazy Loaded) ---
    prompt_refiner_agent = get_agent("PromptRefinerAgent")
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
    logger.info(f"--- 💾 Saving to Memory ({DATABASE_FILE})... ---")
    new_bug_report = {
        "bug_id": f"bug_{uuid.uuid4().hex[:8]}",
        "timestamp": asyncio.get_event_loop().time(),
        "original_prompt": agent_prompt,
        "critique": bug_critique,
        "suggested_fix": suggested_fix,
        "trace": json.loads(trace_json) # Store the trace as an object
    }
    
    try:
        # Re-initialize just in case file was deleted (safety check for cloud/local)
        initialize_database()
        
        with open(DATABASE_FILE, "r+") as f:
            data = json.load(f)
            data.append(new_bug_report)
            f.seek(0)
            json.dump(data, f, indent=2)
        logger.info(f"--- ✅ Bug {new_bug_report['bug_id']} saved to memory. ---")
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"--- ❌ FAILED to save to memory: {e} ---")
        return {"error": "Debug analysis complete, but failed to save to memory."}

    logger.info("--- 🏁 [Step 2: EVOLVE] Manual Debug Loop Complete. ---")
    
    return {
        "critique": bug_critique,
        "suggested_fix": suggested_fix
    }

# --- 5. Define the FastAPI App and Lifespan (Modern Startup) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs ONCE on startup. It is fast because it only checks the DB file,
    # and does NOT initialize the LLM agents.
    initialize_database()
    yield
    # Cleanup on shutdown (not typically needed for Cloud Run, but good practice)

app = FastAPI(lifespan=lifespan)
logger.info("✅ FastAPI App created with lifespan manager.")

# Define the request body structure
class DebugRequest(BaseModel):
    agent_prompt: str
    trace_json: str

# --- 6. Define the Agent Endpoint ---
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

# --- 7. Add Bonus "Memory" Endpoint (Day 3) ---
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

# --- 8. (Local Development Only) ---
if __name__ == "__main__":
    logger.info("🚀 Starting AGENT LENS 2.0 Server (Dev Mode)...")
    # This block is for testing locally. The Dockerfile (for deployment) uses Gunicorn.
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
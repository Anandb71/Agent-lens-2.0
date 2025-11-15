# Agent-Lens 2.0: An AgentOps Debugging Engine

Kaggle Agents Intensive Capstone Project (Submission)

## 1. The Problem: The "Black Box"

In the world of Large Language Model (LLM) agents, the biggest challenge isn't "what happens when it works," but "what happens when it fails?"

Traditional debugging tools fall short. Agents often fail silently, get stuck in loops, or produce non-deterministic errors. Debugging them feels like trying to fix a "black box" from the outside. We need a way to look inside the agent's "mind" at the moment of failure.

## 2. The Solution: Agent-Lens

Agent-Lens is a complete AgentOps (Agent Operations) prototype that solves this problem.

It's a meta-agent system that provides Analysis-as-a-Service. Instead of just crashing, a failing agent can send its final trace to Agent-Lens. Agent-Lens then uses its own set of agents to perform a root cause analysis and suggest a fix.

This project implements a full, end-to-end "Observe -> Evolve" feedback loop.

## 3. Architecture Deep-Dive

This project is a complete client-server application that demonstrates a real-world, scalable architecture.

*   **client.py (The "Observer"):** This script simulates a "production" environment. It runs a `buggy_agent` that is designed to fail. When it does, `client.py` "Observes" the failure by capturing the full agent trace. It then acts as an A2A (Ask-to-Answer) client, sending the failed trace to our server for analysis.
*   **server.py (The "Evolver" / A2A Service):** This is the core Agent-Lens engine, exposed as a FastAPI service. It receives the request from the client and acts as the A2A "Answerer". It doesn't do the thinking itself; instead, it calls our specialized meta-agents.
*   **agents.py (The "Brain"):** This library contains our two specialized meta-agents:
    *   `DebugCriticAgent`: Its only job is to analyze a failed trace and determine the root cause (e.g., "The agent was instructed to use a tool, but no tools were provided.").
    *   `PromptRefinerAgent`: It takes the original prompt and the critic's analysis, and rewrites the prompt to fix the bug (e.g., "Add the 'Google Search' tool to the agent's toolset.").
*   **bug_database.json (The "Memory"):** This is our project's persistent memory. The `server.py` saves every single bug report, critique, and suggested fix to this database. This allows us to track agent failures over time and build a dashboard of our system's health.

## 4. How to Run Agent-Lens

Follow these steps to run the full, end-to-end "Observe -> Evolve" loop.

### Step 1: Install Dependencies

Install all required Python libraries.

```bash
# Make sure you are in the agent_lens_2.0 directory
pip install -r requirements.txt
```

### Step 2: Run the Server (Terminal 1)

In your first terminal, start the Agent-Lens server. It will wait for clients to connect.

```bash
# In Terminal 1:
python server.py
```

```bash
# --- Expected Output ---
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Step 3: Run the Client (Terminal 2)

In a second terminal, set your `GOOGLE_API_KEY` and run the client. The client will run the buggy agent, capture its trace, and send it to the server.

```bash
# In Terminal 2 (PowerShell):
$env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"; python client.py

# In Terminal 2 (bash/zsh):
export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
python client.py
```

### Step 4: See the Results

The `client.py` script will print the server's analysis directly to your console.

```
# --- Expected Client Output ---
# ...
# 🏆 AGENT LENS 2.0: DEBUGGING SERVICE RESPONSE 🏆
# ==================================================
#
# --- CRITIQUE FROM SERVICE ---
# The agent was instructed 'You MUST use the `Google Search` tool to find information', but the `tools` list provided to the agent was empty. This led to a failure as the agent could not fulfill its core instruction.
#
# --- SUGGESTED FIX FROM SERVICE ---
# The agent's prompt is valid, but its configuration is flawed. To fix this, you must provide the agent with the 'Google Search' tool.
#
# Example (in google-adk):
# from google.adk.tools import GoogleSearch
# ...
# buggy_agent = Agent(
#     ...
#     tools=[GoogleSearch()], # <--- ADD THIS
# )
# ==================================================
```

You can also check the server's memory by opening `bug_database.json` or by curling the `/memory` endpoint:

```bash
# In Terminal 2, after running the client:
curl http://127.0.0.1:8000/memory
```

## 5. A Note on the A2A Implementation

My initial plan was to use the ADK's `to_a2a` helper function to build the A2A service.

However, during testing with the provided ADK (v1.18.0), I identified a `ModuleNotFoundError` and version incompatibility that made this helper function unreliable.

To ensure maximum stability and build a production-ready system, I made a deliberate engineering decision to revert to a manual, robust REST API.

*   The Server uses FastAPI to expose a clean `/debug` endpoint.
*   The Client uses `httpx` to send its request.

This approach perfectly implements the "Ask-to-Answer" (A2A) pattern in a framework-agnostic way, guaranteeing that the project runs reliably in any environment.

## 6. Future Vision: From Prototype to Platform

This project is the core engine for a full-scale AgentOps platform. The future possibilities are massive:

*   **CI/CD Integration:** Integrate `client.py` into a GitHub Actions pipeline. Automatically run 100 tests on every commit and get AI-powered bug reports before code even merges.
*   **Self-Healing Agents:** A production agent could use this service to debug itself. A `try/except` block could call the Agent-Lens server on failure, receive a new prompt, and retry the task with the new, corrected instructions.
*   **Visual Dashboard:** A simple web application (e.g., in React or Angular) could read `bug_database.json` and display a live, filterable dashboard of all agent failures, critiques, and fixes over time.

Thank you for reviewing my project.
---

## 7. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
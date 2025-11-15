# AGENT LENS 2.0 - Kaggle 5-Day AI Agents Intensive Capstone Project

Track: D. Freestyle Track

Project: An "AgentOps Meta-Agent" for autonomous debugging and analysis.

## 1. Project Pitch: The "Postman for AI Agents"

This project, Agent Lens 2.0, is an AgentOps Meta-Agent built entirely with the Agent Development Kit (ADK) and concepts from the 5-day intensive course.

While other agents do tasks, our agent fixes agents.

It solves the #1 problem for AI developers: debugging non-deterministic agentic workflows. It functions as an A2A-compliant service that other agents can call when they fail. When an agent sends its failed trace to Agent Lens 2.0, our service:

*   **OBSERVES** the failure by analyzing the trace.
*   **EVOLVES** the agent by using an LLM-as-a-Judge to find the root cause and a RefinerAgent to suggest a code/prompt fix.
*   **REMEMBERS** the bug and its fix in a persistent "bug database" (our Memory).

## 2. Key Course Concepts Demonstrated

This project strategically integrates advanced concepts from all 5 days of the course.

### 📄 Day 1: Orchestration (Manual LoopAgent)

We implemented a manual "Debug & Refine" loop, directly inspired by the LoopAgent codelab.

Our `server.py` orchestrates two specialist agents: a `DebugCriticAgent` and a `PromptRefinerAgent`.

This manual orchestration pattern gives us full control over the "Evolve" loop, passing the critique from the "Critic" to the "Refiner" to generate a fix.

### 📄 Day 3: Persistent Memory (`bug_database.json`)

Our meta-agent features a persistent memory system, as seen in the Day 3 codelab.

The `run_debug_analysis` function saves every bug report (the critique + the fix) to `bug_database.json`.

We exposed this memory via a `/memory` endpoint on our server, proving that our agent "learns" from every bug it diagnoses.

### 📄 Day 4: Observability & LLM-as-a-Judge

**Observability:** The entire project is an "Observability" tool. `client.py` captures a full, failed agent trace (`buggy_runner.get_trace()`) and serializes it to JSON.

**LLM-as-a-Judge:** Our `DebugCriticAgent` acts as a scalable, automated LLM-as-a-Judge. It ingests the failed trace and provides a root cause analysis, demonstrating the "Glass Box" evaluation concept from the whitepaper.

### 📄 Day 5: Prototype to Production (A2A Protocol)

We converted our agent from a simple script into a production-grade A2A (Agent2Agent) Service.

**A2A Server (`server.py`):** We wrapped our core logic in a `FunctionTool` and used `to_a2a()` to expose it as a discoverable agent service on the network.

**A2A Client (`client.py`):** Our client uses `RemoteA2aAgent` to connect to the server's agent card, demonstrating how a "buggy" agent can call our service for autonomous debugging.

## 3. How to Run This Project

This project consists of two main components: the Server (our meta-agent) and the Client (the buggy agent).

### Prerequisites

*   Python 3.10+
*   `pip install -r requirements.txt`
*   Set your Gemini API Key:
    *   (PowerShell): `$env:GOOGLE_API_KEY="your_api_key_here"`
    *   (Mac/Linux): `export GOOGLE_API_KEY='your_api_key_here'`

### Step 1: Run the Server

In your first terminal, start the Agent Lens 2.0 server.

```bash
python agent_lens_2.0/server.py
```

You will see `INFO: Uvicorn running on http://127.0.0.1:8000`. Keep this terminal running.

### Step 2: Run the Client (in a new terminal)

In a new, second terminal, activate the same virtual environment and set your API key. Then, run the client.

```bash
python agent_lens_2.0/client.py
```

### Step 3: See the Results

The client terminal will run, capture a failed trace, call the server, and then print the full debugging results:

```
==================================================
🏆 AGENT LENS 2.0: A2A DEBUGGING RESULTS 🏆
==================================================

--- [CRITIC] ROOT CAUSE (from server) ---
The agent failed because it attempted to call a tool (`Google Search`) that was not available in its tool list...

--- [REFINER] SUGGESTED FIX (from server) ---
You are a helpful research assistant. You MUST use the `search` tool to find information.
==================================================
```

### Step 4: Verify Persistent Memory (Day 3)

In your client terminal, you can now query the server's memory endpoint to see the bug report it just saved:

```bash
# Windows (PowerShell)
curl http://127.0.0.1:8000/memory

# Mac/Linux
curl http://127.0.0.1:8000/memory
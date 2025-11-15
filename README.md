# Agent-Lens 2.0: An AgentOps Debugging Engine

Kaggle Agents Intensive Capstone Project (Submission)

## 1. The Problem: The "Black Box"

In the world of Large Language Model (LLM) agents, the biggest challenge isn't "what happens when it works," but "what happens when it fails?"

Traditional debugging tools fall short. Agents often fail silently, get stuck in loops, or produce non-deterministic errors. Debugging them feels like trying to fix a "black box" from the outside. We need a way to look inside the agent's "mind" at the moment of failure.

## 2. The Solution: Agent-Lens

Agent-Lens is a complete AgentOps (Agent Operations) prototype that solves this problem.

It's a meta-agent system that provides Analysis-as-a-Service. Instead of just crashing, a failing agent can send its final trace to Agent-Lens. Agent-Lens then uses its own set of agents to perform a root cause analysis and suggest a fix.

This project implements a full, end-to-end "Observe → Evolve" feedback loop.

## 3. Architecture Deep-Dive

This project is a complete client-server application demonstrating a real-world, scalable architecture.

*   **client.py (The "Observer"):** Runs the `buggy_agent`, captures its full execution trace on failure, and sends the trace to the cloud service via HTTP.
*   **server.py (The "Evolver" / A2A Service):** A FastAPI service that receives the trace and orchestrates the meta-agent loop.
*   **agents.py (The "Brain"):** Defines the two specialized meta-agents:
    *   `DebugCriticAgent`: Analyzes the trace to determine the single, specific root cause of the failure.
    *   `PromptRefinerAgent`: Takes the critique and suggests a detailed, actionable technical fix (e.g., missing imports, better tool-use logic).
*   **bug_database.json (The "Memory"):** Serves as persistent storage, logging every failure, critique, and fix for historical monitoring.

## 4. Technical Justification: Robustness in the Cloud

To ensure reliable deployment, the final architecture incorporates several critical engineering fixes:

*   **A2A Protocol (Manual REST):** We abandoned the unreliable ADK `to_a2a` helper in favor of a robust, manual REST API using FastAPI and `httpx`. This guarantees stability and demonstrates superior, framework-agnostic communication.
*   **Lazy Loading (Startup Fix):** To fix the Cloud Run Startup Timeout errors, all LLM agent instances were removed from the global scope and implemented with a lazy-loading singleton pattern. Agents are now initialized only when the `/debug` endpoint is hit, allowing the service to become "Ready" quickly.
*   **Memory Optimization:** Due to the resource-intensive nature of running two large LLM agents concurrently, the final service is configured to run with 2GiB of memory to prevent Out-of-Memory (OOM) crashes during execution.
*   **Persistence Fix:** The database file path is dynamically set to `/tmp/bug_database.json` for deployment, ensuring that memory writes succeed in the Cloud Run read-only filesystem.

## 5. Final Test & Deployment Instructions

The following steps prove the functionality of the complete, cloud-deployed engine.

### Step 1: Install Dependencies

```bash
# Make sure you are in the agent_lens_2.0 directory
pip install -r requirements.txt
```

### Step 2: Deploy the Final Service (The Successful Command)

This command deploys the fully fixed code, injecting the necessary environment variables and memory allocation:

```bash
gcloud run deploy agent-lens-service --source . --region us-central1 --set-env-vars=GOOGLE_API_KEY=AIzaSyC2Xkwjno-DmMonrwtCnq8OJK1IrBzzJx4 --memory=2Gi
```

### Step 3: Run the Final Client Test (The Victory Lap)

Once the deployment finishes (Revision 15/16), run the client to observe the full success. (The client's `SERVER_URL` must be updated to the Cloud Run URL).

```bash
$env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"; python client.py
```

**Expected Result:** The client successfully receives an `HTTP/1.1 200 OK` response and prints the full AI-generated critique and suggested fix.

## 6. Future Vision: From Prototype to Platform

This engine is the foundation for:

*   **Self-Healing Agents:** The critique and fix can be fed directly back into an agent's code, creating a truly self-improving system.
*   **CI/CD Integration:** Automated QA pipelines can use the `/debug` endpoint to automatically analyze and report all agent test failures.
*   **Visual Dashboard:** The `/memory` endpoint exposes the entire bug history, ready to be visualized on a web dashboard for AgentOps monitoring.

## 7. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
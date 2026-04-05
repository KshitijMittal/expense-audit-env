import os
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models import Action, Observation
from environment import ExpenseEnvironment, POLICY_TEXT
from tasks import tasks, grade, get_task

load_dotenv()

app = FastAPI(
    title="Expense Report Auditing Environment",
    description="An API for an AI agent to audit employee expense claims.",
    version="1.0.0",
)

# --- AI Client Setup ---
# The API key is loaded from the .env file.
# Ensure you have a .env file with GROQ_API_KEY="your-key-here"
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY"),
)
AI_MODEL = "llama-3.1-8b-instant"
VALID_ACTIONS = {"approve", "reject", "escalate"}

# --- Global Environment ---
# A single environment instance is shared across all API calls.
env = ExpenseEnvironment()


# --- Pydantic Models for Requests ---

class ResetRequest(BaseModel):
    task_id: str


class GraderRequest(BaseModel):
    task_id: str
    decisions: list[str]


# --- API Endpoints ---

@app.post("/reset", summary="Reset Environment", tags=["Environment"])
def reset(req: ResetRequest):
    """
    Resets the environment to the beginning of a specified task.

    - **task_id**: The ID of the task to start (e.g., "task_easy").
    """
    try:
        initial_observation = env.reset(req.task_id)
        return {
            "observation": initial_observation,
            "state": env.state(),
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task ID '{req.task_id}' not found.")


@app.post("/step", summary="Take a Step", tags=["Environment"])
def step(action: Action):
    """
    Submits an agent's decision for the current expense item and moves to the next one.

    - **decision**: The agent's action ("approve", "reject", or "escalate").
    """
    if env.done:
        raise HTTPException(
            status_code=400,
            detail="The episode is over. Please call /reset to start a new one.",
        )

    observation, reward, done, info = env.step(action)

    return {
        "observation": observation,
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state", summary="Get Current State", tags=["Environment"])
def get_current_state():
    """
    Returns the current internal state of the environment.
    """
    return env.state()


@app.get("/tasks", summary="List All Tasks", tags=["Tasks"])
def get_all_tasks():
    """
    Returns a list of all available tasks with their descriptions.
    """
    # We only want to expose the description, not the items and answers
    return {
        task_id: {
            "name": task.get("name", "N/A"),
            "description": task.get("description"),
        }
        for task_id, task in tasks.items()
    }


@app.post("/grader", summary="Grade Agent Performance", tags=["Tasks"])
def run_grader(req: GraderRequest):
    """
    Grades a list of agent decisions against the correct answers for a given task.
    """
    try:
        task = get_task(req.task_id)
        score = grade(req.decisions, task["answers"])
        return {"task_id": req.task_id, "score": score}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task ID '{req.task_id}' not found.")


@app.post("/baseline", summary="Run AI Baseline", tags=["Baseline"])
def run_baseline():
    """
    Runs a baseline AI agent (Groq Llama3-8b) through all tasks and returns the scores.
    This is a blocking call and may take a few moments to complete.
    """
    results = {}

    for task_id in tasks:
        # Reset the environment for the current task
        observation = env.reset(task_id)
        agent_decisions = []
        done = False

        while not done:
            # Generate the prompt for the AI
            prompt = _create_prompt(observation)

            # Call the AI for a decision
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert expense auditor."},
                        {"role": "user", "content": prompt},
                    ],
                    model=AI_MODEL,
                    temperature=0,
                    max_tokens=10,
                )
                ai_decision = chat_completion.choices[0].message.content.strip().lower()

                # Clean and validate the AI's response
                # This ensures we only get one of the three allowed actions
                cleaned_decision = "".join(c for c in ai_decision if c.isalpha())
                if cleaned_decision not in VALID_ACTIONS:
                    cleaned_decision = "escalate" # Default to escalate if response is invalid

            except Exception as e:
                print(f"Error calling Groq API: {e}")
                cleaned_decision = "escalate" # Default to escalate on API error

            agent_decisions.append(cleaned_decision)

            # Take a step in the environment with the AI's decision
            action = Action(decision=cleaned_decision)
            observation, _, done, _ = env.step(action)

        # Grade the performance for the completed task
        task_data = get_task(task_id)
        score = grade(agent_decisions, task_data["answers"])
        results[task_id] = score

    return results

@app.get("/health", summary="Health Check", tags=["System"])
def health():
    return {"status": "healthy"}


@app.get("/metadata", summary="Environment Metadata", tags=["System"])
def metadata():
    return {
        "name": "expense-audit-env",
        "description": "An AI agent audits employee expense claims against company reimbursement policy",
        "version": "1.0.0"
    }


@app.get("/schema", summary="Environment Schema", tags=["System"])
def schema():
    return {
        "action": {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["approve", "reject", "escalate"]
                },
                "reason": {
                    "type": "string",
                    "nullable": True
                }
            },
            "required": ["decision"]
        },
        "observation": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "task_description": {"type": "string"},
                "item_name": {"type": "string"},
                "amount": {"type": "number"},
                "category": {"type": "string"},
                "vendor": {"type": "string"},
                "date_of_expense": {"type": "string"},
                "date_submitted": {"type": "string"},
                "policy": {"type": "string"},
                "history": {"type": "array", "items": {"type": "string"}}
            }
        },
        "state": {
            "type": "object",
            "properties": {
                "current_index": {"type": "integer"},
                "actions": {"type": "array", "items": {"type": "string"}},
                "done": {"type": "boolean"}
            }
        }
    }


@app.post("/mcp", summary="MCP Endpoint", tags=["System"])
def mcp(request: dict = None):
    return {
        "jsonrpc": "2.0",
        "result": {
            "name": "expense-audit-env",
            "description": "Expense report auditing environment for AI agents",
            "version": "1.0.0"
        },
        "id": 1
    }

def _create_prompt(obs: Observation) -> str:
    """Helper function to create a standardized prompt for the AI."""
    item_details = (
        f"Expense Item: {obs.item_name}\n"
        f"Amount: ₹{obs.amount}\n"
        f"Category: {obs.category}\n"
        f"Vendor: {obs.vendor}\n"
        f"Expense Date: {obs.date_of_expense}\n"
        f"Submission Date: {obs.date_submitted}\n"
    )

    history_details = "\n".join(f"- {h}" for h in obs.history) if obs.history else "None"

    return (
        "You are an expense auditor. Your task is to approve, reject, or escalate "
        "expense claims based on the provided policy and the item's details.\n\n"
        "## Company Policy:\n"
        f"{POLICY_TEXT}\n\n"
        "## Expense History (Decisions so far):\n"
        f"{history_details}\n\n"
        "## Current Expense to Audit:\n"
        f"{item_details}\n"
        "Based on all the information, should you 'approve', 'reject', or 'escalate'? "
        "Respond with only one of these three words."
    )
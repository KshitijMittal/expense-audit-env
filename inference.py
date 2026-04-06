import os
import sys
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# --- Configuration ---
load_dotenv()

# These are the REQUIRED variable names per hackathon spec.
# On HF Spaces, set these as Repository Secrets.
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME",   "llama-3.1-8b-instant")
HF_TOKEN     = os.environ.get("HF_TOKEN",     os.environ.get("GROQ_API_KEY", ""))

# The environment server URL — defaults to the Docker port used in HF Spaces.
# Override with ENV_URL env var if running against a remote deployment.
SERVER_URL = os.environ.get("ENV_URL", "http://localhost:7860")

VALID_ACTIONS = {"approve", "reject", "escalate"}

POLICY_TEXT = """
Meal ≤ ₹1000
Travel ≤ ₹5000
Equipment > ₹3000 → Escalate
Max 3 same vendor/week
No weekend entertainment
Submit within 14 days
"""

# --- Validate required config ---
if not HF_TOKEN:
    print("Error: HF_TOKEN (or GROQ_API_KEY) is not set.", file=sys.stderr)
    sys.exit(1)

# --- AI Client — MUST use OpenAI client with above variables ---
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN,
)

# --- Prompt Builder ---
def _create_prompt(obs: dict) -> str:
    item_details = (
        f"Expense Item: {obs['item_name']}\n"
        f"Amount: ₹{obs['amount']}\n"
        f"Category: {obs['category']}\n"
        f"Vendor: {obs['vendor']}\n"
        f"Expense Date: {obs['date_of_expense']}\n"
        f"Submission Date: {obs['date_submitted']}\n"
    )
    history_details = "\n".join(f"- {h}" for h in obs['history']) if obs['history'] else "None"
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

# --- AI Decision ---
def get_ai_decision(observation: dict) -> str:
    prompt = _create_prompt(observation)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert expense auditor."},
                {"role": "user", "content": prompt},
            ],
            model=MODEL_NAME,
            temperature=0,
            max_tokens=10,
        )
        ai_decision = chat_completion.choices[0].message.content.strip().lower()
        cleaned = "".join(c for c in ai_decision if c.isalpha())
        return cleaned if cleaned in VALID_ACTIONS else "escalate"
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}", file=sys.stderr)
        return "escalate"

# --- Main Runner ---
def run_inference():
    final_scores = {}

    with httpx.Client(base_url=SERVER_URL, timeout=60.0) as http_client:
        # Fetch all tasks
        try:
            tasks_response = http_client.get("/tasks")
            tasks_response.raise_for_status()
            tasks = tasks_response.json()
        except Exception as e:
            print(f"[ERROR] Cannot connect to environment server at {SERVER_URL}: {e}", file=sys.stderr)
            sys.exit(1)

        for task_id in tasks:
            # --- [START] log — required by hackathon spec ---
            print(f"[START] task_id={task_id}", flush=True)

            # Reset the environment
            reset_res = http_client.post("/reset", json={"task_id": task_id})
            reset_res.raise_for_status()
            observation = reset_res.json()["observation"]
            done = False
            agent_decisions = []
            step_num = 0

            while not done:
                step_num += 1
                decision = get_ai_decision(observation)
                agent_decisions.append(decision)

                # Step the environment
                step_res = http_client.post("/step", json={"decision": decision})
                step_res.raise_for_status()
                step_data = step_res.json()

                reward = step_data["reward"]["score"]
                done   = step_data["done"]
                observation = step_data["observation"]

                # --- [STEP] log — required by hackathon spec ---
                print(f"[STEP] step={step_num} action={decision} reward={reward} done={done}", flush=True)

            # Grade the task
            grader_res = http_client.post("/grader", json={"task_id": task_id, "decisions": agent_decisions})
            grader_res.raise_for_status()
            score = grader_res.json()["score"]
            final_scores[task_id] = score

            # --- [END] log — required by hackathon spec ---
            print(f"[END] task_id={task_id} score={score:.2f}", flush=True)

    # Summary
    print("\n--- Inference Complete ---")
    for task_id, score in final_scores.items():
        print(f"  {task_id}: {score:.4f}")

if __name__ == "__main__":
    run_inference()
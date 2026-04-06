import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# --- Configuration ---
load_dotenv()
SERVER_URL = "http://localhost:8000"
VALID_ACTIONS = {"approve", "reject", "escalate"}

# --- AI Client Setup (Mirrors main.py) ---
# The API key is loaded from the .env file.
try:
    groq_api_key = os.environ["GROQ_API_KEY"]
    if not groq_api_key or groq_api_key == "<your_api_key>":
        print("Error: GROQ_API_KEY is not set or is invalid.")
        print("Please create a .env file and add your key: GROQ_API_KEY=<your_api_key>")
        exit(1)
except KeyError:
    print("Error: GROQ_API_KEY not found in environment variables.")
    print("Please create a .env file with your key: GROQ_API_KEY=<your_api_key>")
    exit(1)

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=groq_api_key,
)
AI_MODEL = "llama-3.1-8b-instant"

POLICY_TEXT = """
Meal ≤ ₹1000
Travel ≤ ₹5000
Equipment > ₹3000 → Escalate
Max 3 same vendor/week
No weekend entertainment
Submit within 14 days
"""

# --- Helper Functions ---

def _create_prompt(obs: dict) -> str:
    """Helper function to create a standardized prompt for the AI."""
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

def get_ai_decision(observation: dict) -> str:
    """Calls the Groq API to get the AI's decision."""
    prompt = _create_prompt(observation)
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

        # Clean and validate the response
        cleaned_decision = "".join(c for c in ai_decision if c.isalpha())
        if cleaned_decision in VALID_ACTIONS:
            return cleaned_decision
        return "escalate"  # Default to escalate if response is invalid
    except Exception as e:
        print(f"  -> Error calling Groq API: {e}")
        return "escalate"  # Default to escalate on API error

# --- Main Execution Logic ---

def run_baseline():
    """
    Runs the baseline AI agent against the local environment server.
    """
    final_scores = {}
    with httpx.Client(base_url=SERVER_URL, timeout=30.0) as http_client:
        try:
            # 1. Get the list of tasks
            print("Fetching tasks from the server...")
            tasks_response = http_client.get("/tasks")
            tasks_response.raise_for_status()
            tasks = tasks_response.json()
            print(f"Found {len(tasks)} tasks: {', '.join(tasks.keys())}\n")

        except (httpx.ConnectError, httpx.RequestError) as e:
            print(f"Error: Could not connect to the server at {SERVER_URL}.")
            print("Please make sure the FastAPI server is running: uvicorn main:app --port 8000")
            return

        # 2. Loop through each task
        for task_id, task_info in tasks.items():
            print(f"--- Running Task: {task_info.get('name', task_id)} ---")

            # Reset the environment for the task
            reset_res = http_client.post("/reset", json={"task_id": task_id})
            reset_res.raise_for_status()

            observation = reset_res.json()["observation"]
            done = False
            agent_decisions = []

            # 3. Loop through each step in the task
            while not done:
                item_name = observation["item_name"]
                print(f"  Auditing item: '{item_name}'...")

                # Get AI decision
                decision = get_ai_decision(observation)
                agent_decisions.append(decision)
                print(f"    -> AI Decision: {decision.upper()}")

                # Step the environment
                step_payload = {"decision": decision}
                step_res = http_client.post("/step", json=step_payload)
                step_res.raise_for_status()
                step_data = step_res.json()

                # Update state for the next loop
                observation = step_data["observation"]
                done = step_data["done"]

                # Print correctness based on reward score, not string matching
                reward_explanation = step_data["reward"]["explanation"]
                if step_data["done"]:
                    print(f"    -> Result: Final item complete.")
                else:
                    reward_score = step_data["reward"]["score"]
                    if reward_score < 0:
                        print(f"    -> Result: INCORRECT. ({reward_explanation})")
                    else:
                        print(f"    -> Result: CORRECT. ({reward_explanation})")


            # 4. Grade the completed task
            grader_payload = {"task_id": task_id, "decisions": agent_decisions}
            grader_res = http_client.post("/grader", json=grader_payload)
            grader_res.raise_for_status()
            score = grader_res.json()["score"]
            final_scores[task_id] = score
            print(f"  Task '{task_id}' complete. Final Score: {score:.2f}\n")

    # 5. Print final results table
    print("--- Baseline Run Complete ---")
    print("\nFinal Scores:")
    print("-----------------------------")
    print(f"| {'Task':<15} | {'Score':<7} |")
    print("-----------------------------")
    for task_id, score in final_scores.items():
        print(f"| {task_id:<15} | {score:<7.2f} |")
    print("-----------------------------")


if __name__ == "__main__":
    run_baseline()

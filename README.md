# Expense Report Auditing Environment

This project is an AI-powered environment for auditing employee expense reports based on a set of company policies. It is designed as a challenge for the Meta Llama 3 Hackathon, where the goal is to build an AI agent that can accurately and efficiently audit expense claims.

The environment is built with FastAPI and provides a set of API endpoints for an AI agent to interact with. The agent can reset the environment to a specific task, receive expense items one by one, and submit a decision (`approve`, `reject`, or `escalate`) for each.

## How to Run Locally

1.  **Set up Virtual Environment:**
    Create and activate a Python virtual environment.

    ```bash
    # Create the environment
    python -m venv venv

    # Activate on Windows
    .\venv\Scripts\activate

    # Activate on macOS/Linux
    source venv/bin/activate
    ```

2.  **Install Dependencies:**
    Install all required libraries from `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variable:**
    Create a `.env` file in the project root and add your Groq API key.

    ```
    # .env
    GROQ_API_KEY=your_key_here
    ```

    Replace `your_key_here` with your actual key from [groq.com](https://groq.com/).

4.  **Start the Server:**
    Run the FastAPI application using Uvicorn.

    ```bash
    uvicorn main:app --reload --port 8000
    ```

5.  **Access API Docs:**
    Open your browser and navigate to [http://localhost:8000/docs](http://localhost:8000/docs) to see the interactive API documentation.

## How to Run the Baseline Script

The `baseline.py` script runs a pre-built AI agent (using Groq's Llama3-8b) through all the tasks and prints the results.

Make sure the FastAPI server is running in one terminal, then run the following command in a second terminal:

```bash
python baseline.py
```

The script will connect to the local server, run the agent through all tasks, and print a final score summary.

## The Tasks

The environment includes three distinct tasks to evaluate an agent's performance:

- **Easy Audit (`task_easy`):** A short task with 3 expense items and one very obvious policy violation.
- **Medium Audit (`task_medium`):** A task with 5 items designed to test an agent's understanding of multiple, distinct policy rules.
- **Hard Audit (`task_hard`):** A longer task with 9 items that requires the agent to remember previous items (history) to detect pattern-based violations, such as vendor frequency.

## Company Policy Rules

All AI decisions should be based on the following six rules:

| Rule                 | Policy                                                             | Action              |
| :------------------- | :----------------------------------------------------------------- | :------------------ |
| **Meal Limit**       | Meal claims must be **₹1000 or less**.                             | `reject` if over    |
| **Travel Limit**     | Travel claims must be **₹5000 or less**.                           | `reject` if over    |
| **Equipment**        | Equipment over ₹3000 requires manager review.                      | `escalate` if over  |
| **Submission Date**  | Expenses must be submitted within **14 days** of the expense date. | `reject` if late    |
| **Vendor Frequency** | The same vendor cannot be used more than **3 times** in one week.  | `reject` on 4th+    |
| **Entertainment**    | Entertainment expenses on a **weekend** are not reimbursable.      | `reject` if weekend |

## API Endpoints

### `POST /reset`

Resets the environment to the start of a specific task.

**Request:**

```json
{
  "task_id": "task_easy"
}
```

**Response:**

```json
{
  "observation": {
    "task_id": "task_easy",
    "task_description": "Simple expense validation with one clear violation",
    "item_name": "Lunch",
    "amount": 800.0,
    "category": "meal",
    "vendor": "X",
    "date_of_expense": "2026-03-18",
    "date_submitted": "2026-03-19",
    "policy": "\nMeal ≤ ₹1000\nTravel ≤ ₹5000\n...",
    "history": []
  },
  "state": {
    "current_index": 0,
    "actions": [],
    "done": false
  }
}
```

### `POST /step`

Submits an agent's decision for the current item.

**Request:**

```json
{
  "decision": "approve"
}
```

**Response:**

```json
{
  "observation": {
    /* ... next item ... */
  },
  "reward": {
    "score": 1.0,
    "explanation": "Decision: APPROVE | Reason: Valid meal expense",
    "done": false,
    "confidence": 1.0
  },
  "done": false,
  "info": {}
}
```

### `GET /state`

Returns the current state of the environment.

**Response:**

```json
{
  "current_index": 1,
  "actions": ["approve"],
  "done": false
}
```

### `GET /tasks`

Lists all available tasks.

**Response:**

```json
{
  "task_easy": {
    "name": "Easy Audit",
    "description": "3 expense items, one obvious policy violation"
  },
  "task_medium": {
    /* ... */
  },
  "task_hard": {
    /* ... */
  }
}
```

### `POST /grader`

Grades a list of decisions for a task.

**Request:**

```json
{
  "task_id": "task_easy",
  "decisions": ["approve", "reject", "approve"]
}
```

**Response:**

```json
{
  "task_id": "task_easy",
  "score": 1.0
}
```

### `POST /baseline`

Runs the built-in Groq AI agent on all tasks.

**Response:**

```json
{
  "task_easy": 1.0,
  "task_medium": 0.8,
  "task_hard": 0.5555555555555556
}
```

## Baseline Scores

The expected scores from the built-in baseline agent are approximately:

| Task          | Expected Score |
| :------------ | :------------- |
| `task_easy`   | 0.67           |
| `task_medium` | 0.80           |
| `task_hard`   | 0.78           |

_Note: Scores may vary slightly based on AI model updates._

## Environment Variables

- `GROQ_API_KEY`: **Required.** Your API key for the Groq service. The baseline agent will not work without this.

## Deployment

This project includes a `Dockerfile` configured for deployment on services like Hugging Face Spaces.

- The container exposes port **7860**.
- It uses `python:3.11-slim` as the base image.
- Dependencies are installed from `requirements.txt`.
- The application is started with `uvicorn main:app --host 0.0.0.0 --port 7860`.
- A `.dockerignore` file is included to prevent copying unnecessary files like `.env` and `venv/` into the image. You should set your `GROQ_API_KEY` as a secret in your deployment environment.

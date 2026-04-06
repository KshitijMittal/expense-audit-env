---
title: Expense Audit Env
emoji: 🌖
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: AI-powered environment for auditing employee expense reports
---

# Expense Report Auditing Environment

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered environment for auditing employee expense reports based on a set of company policies. This project is designed for AI agent competitions, where the goal is to build an agent that can accurately and efficiently audit expense claims.

## Features

- **Realistic Auditing Tasks:** Includes three tasks (Easy, Medium, Hard) to test an agent's ability to handle various policy violations.
- **Dynamic Policy Engine:** Enforces clear but complex company policies, including spending limits, date restrictions, and pattern-based rules.
- **FastAPI Backend:** A robust and fast API for agent interaction, built with FastAPI.
- **Structured Inference Script:** Includes `inference.py` — the primary agent script — with structured `[START]/[STEP]/[END]` stdout logging for automated evaluation.
- **Dockerized for Deployment:** Comes with a `Dockerfile` ready for deployment on Hugging Face Spaces.

---

## Environment Variables

Set these before running the server or inference script.

| Variable       | Required | Description                                                  |
| :------------- | :------- | :----------------------------------------------------------- |
| `API_BASE_URL` | Yes      | LLM API base URL (e.g., `https://api.groq.com/openai/v1`)   |
| `MODEL_NAME`   | Yes      | Model name to use (e.g., `llama-3.1-8b-instant`)            |
| `HF_TOKEN`     | Yes      | API key for the LLM provider (Groq key or HF token)         |
| `GROQ_API_KEY` | Optional | Legacy fallback for local development with `baseline.py`    |

Create a `.env` file in the project root:
API_BASE_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama-3.1-8b-instant
HF_TOKEN=<your_groq_api_key>
GROQ_API_KEY=<your_groq_api_key>

Get your free API key from [console.groq.com/keys](https://console.groq.com/keys).

---

## How to Run Locally

### 1. Prerequisites

- Python 3.11+
- Docker (optional, for container testing)

### 2. Set Up Virtual Environment
```bash
# Create the environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file as described in the **Environment Variables** section above.

### 5. Start the Server

Run the FastAPI application using Uvicorn. The server runs on port `7860` to match the Docker and Hugging Face Spaces configuration.
```bash
uvicorn main:app --host 0.0.0.0 --port 7860
```

Once running, the interactive API documentation is available at:
[http://localhost:7860/docs](http://localhost:7860/docs)

---

## Running the Scripts

### `inference.py` — Primary Submission Script

This is the main agent script used for evaluation. It runs an AI agent through all three tasks and emits structured stdout logs in the required `[START]/[STEP]/[END]` format.

With the server running on port `7860` in one terminal, run in a second terminal:
```bash
python inference.py
```

**Expected output format:**
[START] task_id=task_easy
[STEP] step=1 action=approve reward=1.0 done=False
[STEP] step=2 action=reject reward=1.0 done=False
[STEP] step=3 action=approve reward=1.0 done=True
[END] task_id=task_easy score=0.6667
[START] task_id=task_medium
...
[END] task_id=task_medium score=0.8000
[START] task_id=task_hard
...
[END] task_id=task_hard score=0.7778

### `baseline.py` — Local Development Script

This is a simpler alternative script for local testing only. It connects to `localhost:7860`, uses `GROQ_API_KEY` directly, and prints a human-readable summary. It is **not** used for evaluation.
```bash
python baseline.py
```

---

## The Tasks

The environment includes three tasks with increasing difficulty:

| Task | ID | Items | Description |
| :--- | :--- | :---: | :--- |
| Easy Audit | `task_easy` | 3 | One obvious policy violation |
| Medium Audit | `task_medium` | 5 | Multiple distinct rule violations |
| Hard Audit | `task_hard` | 9 | Pattern-based violations requiring memory across items |

---

## Action & Observation Space

### Action Space

The agent must respond with exactly one of three string values per expense item:

| Action     | Meaning                                                |
| :--------- | :----------------------------------------------------- |
| `approve`  | The expense is valid and should be reimbursed.         |
| `reject`   | The expense violates policy and is denied.             |
| `escalate` | The expense requires human/manager review.             |

### Observation Space

Each step returns an observation with the following fields:

| Field              | Type       | Description                                       |
| :----------------- | :--------- | :------------------------------------------------ |
| `task_id`          | `string`   | Identifier of the current task                    |
| `task_description` | `string`   | Human-readable description of the task            |
| `item_name`        | `string`   | Name of the expense item (e.g., "Lunch")          |
| `amount`           | `float`    | Claimed amount in Indian Rupees (₹)               |
| `category`         | `string`   | One of: `meal`, `travel`, `equipment`, `entertainment` |
| `vendor`           | `string`   | Vendor or supplier name                           |
| `date_of_expense`  | `string`   | Date the expense was incurred (`YYYY-MM-DD`)      |
| `date_submitted`   | `string`   | Date the claim was submitted (`YYYY-MM-DD`)       |
| `policy`           | `string`   | Full company policy text for reference            |
| `history`          | `string[]` | List of decisions made so far in this episode     |

---

## Company Policy Rules

All agent decisions must be based on these six rules:

| Rule                | Policy                                                              | Action             |
| :------------------ | :------------------------------------------------------------------ | :----------------- |
| **Meal Limit**      | Meal claims must be **₹1000 or less**.                              | `reject` if over   |
| **Travel Limit**    | Travel claims must be **₹5000 or less**.                            | `reject` if over   |
| **Equipment**       | Equipment over ₹3000 requires manager review.                       | `escalate` if over |
| **Submission Date** | Expenses must be submitted within **14 days** of the expense date.  | `reject` if late   |
| **Vendor Frequency**| The same vendor cannot appear more than **3 times** in one week.    | `reject` on 4th+   |
| **Entertainment**   | Entertainment expenses on a **weekend** are not reimbursable.       | `reject` if weekend|

---

## Baseline Scores

The expected scores from the built-in baseline agent (`inference.py`):

| Task          | Expected Score |
| :------------ | :------------- |
| `task_easy`   | 0.67           |
| `task_medium` | 0.80           |
| `task_hard`   | 0.78           |

_Note: Scores may vary slightly based on AI model behaviour._

---

## API Endpoints

### `POST /reset`

Resets the environment to the start of a specific task.

**Request:**
```json
{ "task_id": "task_easy" }
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
  "state": { "current_index": 0, "actions": [], "done": false }
}
```

### `POST /step`

Submits an agent's decision for the current item.

**Request:**
```json
{ "decision": "approve" }
```

**Response:**
```json
{
  "observation": { },
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
{ "current_index": 1, "actions": ["approve"], "done": false }
```

### `GET /tasks`

Lists all available tasks.

**Response:**
```json
{
  "task_easy":  { "name": "Easy Audit",   "description": "3 expense items, one obvious policy violation" },
  "task_medium": { "name": "Medium Audit", "description": "5 items testing multiple policy rules" },
  "task_hard":  { "name": "Hard Audit",   "description": "9 items requiring pattern detection across the full episode" }
}
```

### `POST /grader`

Grades a list of decisions for a task.

**Request:**
```json
{ "task_id": "task_easy", "decisions": ["approve", "reject", "approve"] }
```

**Response:**
```json
{ "task_id": "task_easy", "score": 1.0 }
```

### `POST /baseline`

Runs the built-in AI agent on all tasks via the server.

**Response:**
```json
{ "task_easy": 0.67, "task_medium": 0.80, "task_hard": 0.78 }
```

### `GET /health`

Returns server health status.

**Response:**
```json
{ "status": "healthy" }
```

---

## Deployment

This project is deployed on Hugging Face Spaces using Docker.

- Container exposes port **7860**
- Base image: `python:3.11-slim`
- Dependencies installed from `requirements.txt`
- Server started with: `uvicorn main:app --host 0.0.0.0 --port 7860`
- Set `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` as Repository Secrets in your HF Space settings — never commit them to the repo.
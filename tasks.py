from typing import List, Dict


# -------- TASK DATA -------- #

tasks = {
    "task_easy": {
        "name": "Easy Audit",
        "description": "Simple expense validation with one clear violation",
        "items": [
            {
                "name": "Lunch",
                "amount": 800,
                "category": "meal",
                "vendor": "X",
                "date_of_expense": "2026-03-18",
                "date_submitted": "2026-03-19"
            },
            {
                "name": "Dinner",
                "amount": 1200,
                "category": "meal",
                "vendor": "Y",
                "date_of_expense": "2026-03-18",
                "date_submitted": "2026-03-19"
            },
            {
                "name": "Taxi",
                "amount": 3000,
                "category": "travel",
                "vendor": "Z",
                "date_of_expense": "2026-03-18",
                "date_submitted": "2026-03-19"
            },
        ],
        "answers": ["approve", "reject", "approve"],
    },

    "task_medium": {
        "name": "Medium Audit",
        "description": "Multiple rule violations across categories",
        "items": [
            {
                "name": "Meal",
                "amount": 900,
                "category": "meal",
                "vendor": "A",
                "date_of_expense": "2026-03-18",
                "date_submitted": "2026-03-19"
            },
            {
                "name": "Flight",
                "amount": 6000,
                "category": "travel",
                "vendor": "B",
                "date_of_expense": "2026-03-18",
                "date_submitted": "2026-03-19"
            },
            {
                "name": "Meal Wrong Category",
                "amount": 1200,  # ✅ FIXED (now actually invalid)
                "category": "meal",
                "vendor": "C",
                "date_of_expense": "2026-03-18",
                "date_submitted": "2026-03-19"
            },
            {
                "name": "Late Travel",
                "amount": 2000,
                "category": "travel",
                "vendor": "D",
                "date_of_expense": "2026-03-01",
                "date_submitted": "2026-03-20"
            },
            {
                "name": "Equipment",
                "amount": 2000,
                "category": "equipment",
                "vendor": "E",
                "date_of_expense": "2026-03-18",
                "date_submitted": "2026-03-19"
            },
        ],
        "answers": ["approve", "reject", "reject", "reject", "approve"],
    },

    "task_hard": {
        "name": "Hard Audit",
        "description": "Pattern-based violations requiring memory",
        "items": [
            {"name": "Meal 1", "amount": 800, "category": "meal", "vendor": "A", "date_of_expense": "2026-03-17", "date_submitted": "2026-03-18"},
            {"name": "Meal 2", "amount": 900, "category": "meal", "vendor": "A", "date_of_expense": "2026-03-18", "date_submitted": "2026-03-19"},
            {"name": "Meal 3", "amount": 750, "category": "meal", "vendor": "A", "date_of_expense": "2026-03-19", "date_submitted": "2026-03-20"},
            {"name": "Meal 4", "amount": 850, "category": "meal", "vendor": "A", "date_of_expense": "2026-03-20", "date_submitted": "2026-03-21"},
            {"name": "Meal 5", "amount": 700, "category": "meal", "vendor": "A", "date_of_expense": "2026-03-21", "date_submitted": "2026-03-22"},

            {
                "name": "Weekend Movie",
                "amount": 500,
                "category": "entertainment",
                "vendor": "B",
                "date_of_expense": "2026-03-22",
                "date_submitted": "2026-03-23"
            },

            {"name": "Travel 1", "amount": 4000, "category": "travel", "vendor": "C", "date_of_expense": "2026-03-18", "date_submitted": "2026-03-19"},
            {"name": "Travel 2", "amount": 3500, "category": "travel", "vendor": "D", "date_of_expense": "2026-03-18", "date_submitted": "2026-03-19"},
            {"name": "Equipment", "amount": 2500, "category": "equipment", "vendor": "E", "date_of_expense": "2026-03-18", "date_submitted": "2026-03-19"},
        ],
        "answers": [
            "approve", "approve", "approve", "reject", "reject",
            "reject",
            "approve", "approve", "approve"
        ],
    },
}


def get_task(task_id: str) -> Dict:
    return tasks.get(task_id)


def grade(actions: List[str], correct_answers: List[str]) -> float:
    correct = 0
    for a, b in zip(actions, correct_answers):
        if a.lower() == b.lower():
            correct += 1
    return correct / len(correct_answers)
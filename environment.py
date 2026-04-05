from models import Observation, Action, Reward
from tasks import get_task, grade
from policy import (
    check_meal_limit,
    check_travel_limit,
    check_equipment,
    check_submission_date,
    check_weekend,
    check_vendor_frequency
)


POLICY_TEXT = """
Meal ≤ ₹1000
Travel ≤ ₹5000
Equipment > ₹3000 → Escalate
Max 3 same vendor/week
No weekend entertainment
Submit within 14 days
"""


class ExpenseEnvironment:
    def __init__(self):
        self.current_task = None
        self.current_index = 0
        self.actions = []
        self.done = False
        self.vendor_history = []

    def reset(self, task_id: str):
        self.current_task = get_task(task_id)
        self.current_index = 0
        self.actions = []
        self.done = False
        self.vendor_history = []

        item = self.current_task["items"][self.current_index]

        return Observation(
            task_id=task_id,
            task_description=self.current_task["description"],
            item_name=item["name"],
            amount=item["amount"],
            category=item["category"],
            vendor=item.get("vendor", "N/A"),
            date_of_expense=item.get("date_of_expense", "2026-03-20"),
            date_submitted=item.get("date_submitted", "2026-03-21"),
            policy=POLICY_TEXT,
            history=[]
        )

    def evaluate_policy(self, item):
        category = item["category"]
        amount = item["amount"]
        vendor = item.get("vendor", "N/A")

        date_of_expense = item.get("date_of_expense", "2026-03-20")
        date_submitted = item.get("date_submitted", "2026-03-21")

        # Submission date rule
        if not check_submission_date(date_of_expense, date_submitted):
            return "reject", "Submitted after 14 days"

        # Vendor frequency rule (checked BEFORE adding current vendor)
        if not check_vendor_frequency(vendor, self.vendor_history):
            return "reject", "Vendor used too frequently"

        # Category rules
        if category == "meal":
            if not check_meal_limit(amount):
                return "reject", "Exceeds meal limit"
            return "approve", "Valid meal expense"

        elif category == "travel":
            if not check_travel_limit(amount):
                return "reject", "Exceeds travel limit"
            return "approve", "Valid travel expense"

        elif category == "equipment":
            decision = check_equipment(amount)
            if decision == "escalate":
                return "escalate", "Requires approval (high amount)"
            return "approve", "Valid equipment expense"

        elif category == "entertainment":
            if not check_weekend(date_of_expense):
                return "reject", "Weekend entertainment not allowed"
            return "approve", "Valid entertainment expense"

        return "approve", "No rule violation"

    def step(self, action: Action):
        if self.done:
            return None

        item = self.current_task["items"][self.current_index]
        correct_decision, explanation = self.evaluate_policy(item)

        self.actions.append(action.decision)

        # Vendor frequency note:
        # We append AFTER checking, so count reflects previous uses only
        self.vendor_history.append(item.get("vendor", "N/A"))

        # Reward logic
        if action.decision.lower() == correct_decision:
            reward_score = 1.0
            reward_text = f"Decision: {correct_decision.upper()} | Reason: {explanation}"
            confidence = 1.0
        else:
            reward_score = -1.0
            reward_text = f"Expected: {correct_decision.upper()} | Reason: {explanation}"
            confidence = 0.5

        self.current_index += 1

        # Final step
        if self.current_index >= len(self.current_task["items"]):
            self.done = True

            final_score = grade(self.actions, self.current_task["answers"])

            last_item = item

            observation = Observation(
                task_id="",
                task_description=self.current_task["description"],
                item_name=last_item["name"],
                amount=last_item["amount"],
                category=last_item["category"],
                vendor=last_item.get("vendor", "N/A"),
                date_of_expense=last_item.get("date_of_expense", "2026-03-20"),
                date_submitted=last_item.get("date_submitted", "2026-03-21"),
                policy=POLICY_TEXT,
                history=self.actions
            )

            return observation, Reward(
                score=final_score,
                explanation="Final evaluation complete",
                done=True,
                confidence=1.0
            ), True, {}

        # Next step
        next_item = self.current_task["items"][self.current_index]

        observation = Observation(
            task_id="",
            task_description=self.current_task["description"],
            item_name=next_item["name"],
            amount=next_item["amount"],
            category=next_item["category"],
            vendor=next_item.get("vendor", "N/A"),
            date_of_expense=next_item.get("date_of_expense", "2026-03-20"),
            date_submitted=next_item.get("date_submitted", "2026-03-21"),
            policy=POLICY_TEXT,
            history=self.actions
        )

        reward = Reward(
            score=reward_score,
            explanation=reward_text,
            done=False,
            confidence=confidence
        )

        return observation, reward, False, {}

    def state(self):
        return {
            "current_index": self.current_index,
            "actions": self.actions,
            "done": self.done
        }
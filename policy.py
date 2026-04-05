from datetime import datetime

# ---- POLICY CONSTANTS ----
MEAL_LIMIT = 1000
TRAVEL_LIMIT = 5000
EQUIPMENT_ESCALATION = 3000
MAX_VENDOR_PER_WEEK = 3
MAX_SUBMISSION_DAYS = 14


# ---- RULE CHECK FUNCTIONS ----

def check_meal_limit(amount):
    return amount <= MEAL_LIMIT


def check_travel_limit(amount):
    return amount <= TRAVEL_LIMIT


def check_equipment(amount):
    if amount > EQUIPMENT_ESCALATION:
        return "escalate"
    return "approve"


def check_submission_date(date_of_expense, date_submitted):
    d1 = datetime.strptime(date_of_expense, "%Y-%m-%d")
    d2 = datetime.strptime(date_submitted, "%Y-%m-%d")
    diff = (d2 - d1).days
    return diff <= MAX_SUBMISSION_DAYS


def check_weekend(date_of_expense):
    d = datetime.strptime(date_of_expense, "%Y-%m-%d")
    return d.weekday() < 5  # True = weekday, False = weekend


def check_vendor_frequency(vendor, history):
    count = history.count(vendor)
    return count < MAX_VENDOR_PER_WEEK
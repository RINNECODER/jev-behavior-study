"""Repeat the user's two car-washing prerequisite questions in one request."""
from flat_earth_benchmark import main

PAYLOAD = {
    "model": "jev-1.13.0",
    "state": "I want to have my car washed at a car wash located a 5-minute walk from my home.",
    "questions": {
        "A": {
            "type": "choice",
            "instructions": "Does my car need to be physically present at the car wash to be washed there?",
            "criteria": {"yes": "Yes", "no": "No", "cannot_be_determined": "Cannot be determined"},
        },
        "B": {
            "type": "choice",
            "instructions": "If I walk to the car wash and leave my car at home, will that accomplish my goal of getting my car washed there?",
            "criteria": {"yes": "Yes", "no": "No", "cannot_be_determined": "Cannot be determined"},
        },
    },
}

if __name__ == "__main__":
    main(payload=PAYLOAD, run_name="carwash-decomposed", expected={"A": "yes", "B": "no"})

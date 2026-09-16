"""Repeat the explicit car-washing question in 1,000 isolated inputs."""
from flat_earth_benchmark import main

PAYLOAD = {
    "model": "jev-latest",
    "state": "",
    "questions": {
        "answer": {
            "type": "choice",
            "instructions": "I need to wash my car. The car wash is a 5-minute walk from my home. Should I walk or drive there?",
            "criteria": {"walk": "Walk", "drive": "Drive"},
        }
    },
}

if __name__ == "__main__":
    main(payload=PAYLOAD, run_name="carwash-explicit")

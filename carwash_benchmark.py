"""Run 1,000 context-free walk/drive carwash questions against Jev."""
from flat_earth_benchmark import main

PAYLOAD = {
    "model": "jev-latest",
    "state": "",
    "questions": {
        "answer": {
            "type": "choice",
            "instructions": "I'm going to the carwash and it's really close, should I walk or should I drive? Answer only walk or drive.",
            "criteria": {"walk": "Walk", "drive": "Drive"},
        }
    },
}

if __name__ == "__main__":
    main(payload=PAYLOAD, run_name="carwash")

"""Run 1,000 context-free letter-count questions against Jev."""
from flat_earth_benchmark import main

WORD = "straberry"
PAYLOAD = {
    "model": "jev-latest",
    "state": "",
    "questions": {
        "answer": {
            "type": "choice",
            "instructions": "How many R's are in straberry? Answer only with the number.",
            "criteria": {str(n): str(n) for n in range(11)},
        }
    },
}

if __name__ == "__main__":
    main(payload=PAYLOAD, run_name="straberry")

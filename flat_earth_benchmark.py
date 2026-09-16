"""Repeat configured choice questions in separate Jev API requests."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
from token_usage import aggregate_usage

ROOT = Path(__file__).resolve().parent
PAYLOAD = {
    "model": "jev-latest",
    "state": "",
    "questions": {
        "answer": {
            "type": "choice",
            "instructions": "Is the Earth flat? Answer only yes or no.",
            "criteria": {"yes": "Yes", "no": "No"},
        }
    },
}


def main(payload=PAYLOAD, run_name="flat-earth", expected=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.count < 1 or args.workers < 1:
        parser.error("count and workers must be positive")
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                name, value = line.split("=", 1)
                os.environ.setdefault(name.strip(), value.strip().strip("\"'"))
    key = os.environ["TYPESAFE_API_KEY"]
    questions = payload["questions"]
    multiple = len(questions) > 1
    choices = tuple(next(iter(questions.values()))["criteria"])
    if expected is not None and (set(expected) != set(questions) or any(expected[k] not in questions[k]["criteria"] for k in expected)):
        parser.error("expected answers must match the questions and their choices")
    body = json.dumps(payload).encode()
    digest = hashlib.sha256(body).hexdigest()
    out = ROOT / "results" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + run_name)
    out.mkdir(parents=True)
    manifest = {
        "requested_trials": args.count,
        "workers": args.workers,
        "payload": payload,
        "payload_sha256": digest,
        "method": "One fresh HTTP request/opener per trial; no cookies, sessions, tools, memory, retries, or previous responses in input. Trial IDs are local only. All configured questions are sent together in each request.",
        "expected": expected,
        "limitations": "Input isolation only, not separate provider containers. Provider caching, hidden context, sampling and statistical independence cannot be verified. Fixed option order. No sampling controls supplied.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Saving:", out, flush=True)

    def trial(index):
        start = time.perf_counter()
        row = {"trial": index, "payload_sha256": digest,
               "started_at": datetime.now(timezone.utc).isoformat()}
        request = urllib.request.Request(
            "https://api.typesafe.ai/v1/systemone", data=body,
            headers={"Authorization": "Bearer " + key,
                     "Content-Type": "application/json", "Cache-Control": "no-cache"})
        try:
            with urllib.request.build_opener().open(request, timeout=45) as response:
                raw = response.read().decode()
                row.update(http_status=response.status, raw_response=raw)
                parsed = json.loads(raw)
            row["response"] = parsed
            row["question_results"] = {}
            for name, question in questions.items():
                answer = parsed.get("answers", {}).get(name, {})
                choice = answer.get("choice")
                row["question_results"][name] = choice if answer.get("type") == "choice" and choice in question["criteria"] else "invalid"
            if multiple:
                row["result"] = "invalid" if "invalid" in row["question_results"].values() else "valid"
            else:
                row["result"] = next(iter(row["question_results"].values()))
            if expected is not None:
                row["all_correct"] = all(row["question_results"][k] == v for k, v in expected.items())
        except urllib.error.HTTPError as error:
            row.update(result="error", http_status=error.code,
                       error=error.read().decode(errors="replace").replace(key, "[REDACTED]"))
        except (urllib.error.URLError, TimeoutError, ValueError, AttributeError, OSError) as error:
            row.update(result="error", error=str(error).replace(key, "[REDACTED]"))
        row["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        return row

    rows = []
    # Validate the actual first trial before dispatching the remaining requests.
    # It counts toward the total; no extra live probes or automatic retries.
    with (out / "results.jsonl").open("w") as output:
        def record(row):
            rows.append(row)
            output.write(json.dumps(row) + "\n")
            output.flush()
            if len(rows) == 1 or len(rows) % 100 == 0:
                print(len(rows), dict(Counter(r["result"] for r in rows)), flush=True)
        record(trial(1))
        if rows[0]["result"] != "error":
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                for row in pool.map(trial, range(2, args.count + 1)):
                    record(row)
    counts = Counter(row["result"] for row in rows)
    usage = aggregate_usage(rows)
    summary = {
        "model_requested": payload["model"],
        "question": " | ".join(q["instructions"] for q in questions.values()),
        "questions_per_request": len(questions),
        "requested_trials": args.count,
        "attempted_trials": len(rows),
        "counts": {label: counts[label] for label in (*(("valid",) if multiple else choices), "invalid", "error")},
        "percent_of_valid_answers": {label: (100 * counts[label] / sum(counts[c] for c in choices)) if sum(counts[c] for c in choices) else None for label in choices},
        "models_returned": dict(Counter(str(r.get("response", {}).get("model")) for r in rows if "response" in r)),
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "total_tokens": usage["total_tokens"],
        "token_usage": usage,
        "limitations": manifest["limitations"],
    }
    if multiple:
        summary.pop("percent_of_valid_answers")
        summary["per_question"] = {}
        for name, question in questions.items():
            selected = Counter(r.get("question_results", {}).get(name, "error") for r in rows)
            details = {"instructions": question["instructions"], "counts": {k: selected[k] for k in (*question["criteria"], "invalid", "error")}}
            if expected is not None:
                details.update(expected=expected[name], correct=selected[expected[name]], accuracy_percent=100 * selected[expected[name]] / len(rows))
            summary["per_question"][name] = details
    if expected is not None:
        summary["all_correct_requests"] = sum(r.get("all_correct", False) for r in rows)
        summary["all_correct_percent"] = 100 * summary["all_correct_requests"] / len(rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)
    if len(rows) != args.count or counts["error"] or counts["invalid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

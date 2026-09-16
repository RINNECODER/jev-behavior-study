"""Aggregate API-reported usage; refresh saved question-test summaries offline."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def aggregate_usage(rows):
    result = {"requests": len(rows)}
    for field in ("input_tokens", "output_tokens"):
        values = [r.get("response", {}).get("usage", {}).get(field) for r in rows]
        reported = [v for v in values if type(v) is int and v >= 0]
        result[field] = sum(reported) if reported else None
        result[field + "_reported_requests"] = len(reported)
        result[field + "_missing_requests"] = len(rows) - len(reported)
        result[field + "_per_reported_request"] = sum(reported) / len(reported) if reported else None
    result["total_tokens"] = (
        result["input_tokens"] + result["output_tokens"]
        if rows and all(result[f + "_missing_requests"] == 0 for f in ("input_tokens", "output_tokens"))
        else None
    )
    return result


def refresh():
    runs = []
    all_rows = []
    for manifest_path in sorted((ROOT / "results").glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        if "payload" not in manifest or "requested_trials" not in manifest:
            continue
        directory = manifest_path.parent
        summary_path = directory / "summary.json"
        if not summary_path.exists():
            continue
        rows = [json.loads(line) for line in (directory / "results.jsonl").read_text().splitlines()]
        usage = aggregate_usage(rows)
        summary = json.loads(summary_path.read_text())
        summary.update(input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
                       total_tokens=usage["total_tokens"], token_usage=usage)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
        runs.append({"run": directory.name, "question": summary["question"],
                     "questions_per_request": len(manifest["payload"]["questions"]), **usage})
        all_rows.extend(rows)
    report = {"source": "API-reported usage in saved responses; missing usage is unknown, not zero.",
              "runs": runs, "totals": aggregate_usage(all_rows)}
    (ROOT / "results" / "question_token_usage.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# Question-test token usage", "",
             "API-reported tokens from saved responses. No new API requests were made.", "",
             "| Run | Requests | Input tokens | Output tokens | Input/request | Output/request |",
             "|---|---:|---:|---:|---:|---:|"]
    for run in runs:
        fields = [run[k] for k in ("requests", "input_tokens", "output_tokens", "input_tokens_per_reported_request", "output_tokens_per_reported_request")]
        lines.append("| " + run["run"] + " | " + " | ".join("Unknown" if v is None else f"{v:,g}" for v in fields) + " |")
    totals = report["totals"]
    lines += ["", f"Known totals: {totals['input_tokens']:,} input tokens and {totals['output_tokens']:,} output tokens.",
              "", "Failed attempts without usage are marked unknown. Averages use only requests reporting the corresponding field.",
              "", "For multi-question tests, usage is for the combined request; the API does not report tokens separately for each question.",
              "", "Run `python token_usage.py` to refresh this report. Future question runs record both token types in their summaries automatically."]
    (ROOT / "TOKEN_USAGE.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    refresh()

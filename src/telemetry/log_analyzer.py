import argparse
import glob
import json
import os
from collections import Counter
from statistics import mean
from typing import Any, Dict, List


def load_log_events(log_dir: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(log_dir, "*.log"))):
        with open(path, encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "event" in entry and "data" in entry:
                    events.append(entry)
    return events


def summarize_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    llm_metrics = [e["data"] for e in events if e["event"] == "LLM_METRIC"]
    agent_ends = [e["data"] for e in events if e["event"] == "AGENT_END"]
    failures = [e["data"] for e in events if e["event"] == "AGENT_FAILURE"]

    summary: Dict[str, Any] = {
        "total_sessions": len(agent_ends),
        "total_failures": len(failures),
        "failure_rate": None,
        "average_prompt_tokens": None,
        "average_completion_tokens": None,
        "average_total_tokens": None,
        "average_latency_ms": None,
        "average_steps": None,
        "failure_codes": {},
    }

    if agent_ends:
        summary["average_steps"] = mean([d.get("steps", 0) for d in agent_ends])
        summary["failure_rate"] = round(len(failures) / len(agent_ends), 4)

    if llm_metrics:
        summary["average_prompt_tokens"] = round(mean([m.get("prompt_tokens", 0) for m in llm_metrics]), 2)
        summary["average_completion_tokens"] = round(mean([m.get("completion_tokens", 0) for m in llm_metrics]), 2)
        summary["average_total_tokens"] = round(mean([m.get("total_tokens", 0) for m in llm_metrics]), 2)
        summary["average_latency_ms"] = round(mean([m.get("latency_ms", 0) for m in llm_metrics]), 2)

    if failures:
        summary["failure_codes"] = dict(Counter([f.get("code", "UNKNOWN") for f in failures]))

    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    print("=== Log Evaluation Summary ===")
    print(f"Total agent sessions: {summary['total_sessions']}")
    print(f"Total failures: {summary['total_failures']}")
    print(f"Failure rate: {summary['failure_rate']}")
    print(f"Average loop steps: {summary['average_steps']}")
    print(f"Average prompt tokens: {summary['average_prompt_tokens']}")
    print(f"Average completion tokens: {summary['average_completion_tokens']}")
    print(f"Average total tokens: {summary['average_total_tokens']}")
    print(f"Average latency (ms): {summary['average_latency_ms']}")
    print("Failure codes:")
    for code, count in summary["failure_codes"].items():
        print(f"  - {code}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze agent telemetry logs.")
    parser.add_argument("--log-dir", default="logs", help="Directory containing JSON log files.")
    args = parser.parse_args()

    if not os.path.isdir(args.log_dir):
        raise FileNotFoundError(f"Log directory not found: {args.log_dir}")

    events = load_log_events(args.log_dir)
    summary = summarize_metrics(events)
    print_summary(summary)


if __name__ == "__main__":
    main()

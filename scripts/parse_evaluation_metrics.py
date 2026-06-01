import json
from collections import Counter
from pathlib import Path
from statistics import mean

PROMPT_LOG_ROOT = Path("logs/system_prompts")
CHAT_LOG_ROOT = Path("logs/chat_events")


def load_log_files(root: Path):
    if not root.exists():
        print(f"Log directory not found: {root}")
        return []

    files = list(root.rglob("*.json"))
    print(f"Found {len(files)} log files in {root}")
    records = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                records.append(json.load(f))
        except Exception as exc:
            print(f"Failed to load {path}: {exc}")
    return records


def safe_get(d, key, default=0):
    return d.get(key, default) if isinstance(d, dict) else default


def aggregate_prompt_records(records):
    metrics = {
        "total_prompt_sessions": len(records),
        "tool_event_count": [],
        "tool_errors": 0,
        "tool_error_by_tool": Counter(),
        "tool_counts": Counter(),
        "estimated_total_tokens": [],
    }

    for record in records:
        metrics["estimated_total_tokens"].append(safe_get(record, "estimated_total_tokens"))
        tool_events = record.get("tool_events", []) or []
        metrics["tool_event_count"].append(len(tool_events))

        for event in tool_events:
            name = event.get("name", "unknown_tool")
            metrics["tool_counts"][name] += 1
            status = event.get("status", "ok")
            if status != "ok":
                metrics["tool_errors"] += 1
                metrics["tool_error_by_tool"][name] += 1

    return metrics


def aggregate_chat_records(records):
    metrics = {
        "total_chat_sessions": len(records),
        "latencies": [],
        "input_tokens": [],
        "output_tokens": [],
    }

    for record in records:
        metrics["latencies"].append(safe_get(record, "latency_ms"))
        metrics["input_tokens"].append(safe_get(record, "input_tokens"))
        metrics["output_tokens"].append(safe_get(record, "output_tokens"))

    return metrics


def agg(values):
    values = [v for v in values if isinstance(v, (int, float))]
    if not values:
        return 0, 0, 0
    return min(values), mean(values), max(values)


def summarize(prompt_metrics, chat_metrics):
    print("Evaluation Metrics Summary")
    print("===========================\n")

    print(f"Prompt logs: {prompt_metrics['total_prompt_sessions']} sessions")
    print(f"Chat logs: {chat_metrics['total_chat_sessions']} sessions\n")

    if prompt_metrics["total_prompt_sessions"] > 0:
        lo, avg, hi = agg(prompt_metrics["estimated_total_tokens"])
        print(f"Estimated prompt tokens: min={lo}, avg={avg:.1f}, max={hi}")
        lo, avg, hi = agg(prompt_metrics["tool_event_count"])
        print(f"Tool events per session: min={lo}, avg={avg:.2f}, max={hi}")
        print(f"Total tool events: {sum(prompt_metrics['tool_event_count'])}")
        print(f"Tool errors: {prompt_metrics['tool_errors']}\n")

        if prompt_metrics["tool_counts"]:
            print("Tool usage breakdown:")
            for tool, count in prompt_metrics["tool_counts"].most_common():
                print(f"- {tool}: {count}")

        if prompt_metrics["tool_error_by_tool"]:
            print("\nTool error breakdown:")
            for tool, count in prompt_metrics["tool_error_by_tool"].most_common():
                print(f"- {tool}: {count}")

    if chat_metrics["total_chat_sessions"] > 0:
        lo, avg, hi = agg(chat_metrics["latencies"])
        print(f"\nLatency (ms): min={lo}, avg={avg:.1f}, max={hi}")
        lo, avg, hi = agg(chat_metrics["input_tokens"])
        print(f"Input tokens: min={lo}, avg={avg:.1f}, max={hi}")
        lo, avg, hi = agg(chat_metrics["output_tokens"])
        print(f"Output tokens: min={lo}, avg={avg:.1f}, max={hi}")


def main():
    prompt_records = load_log_files(PROMPT_LOG_ROOT)
    chat_records = load_log_files(CHAT_LOG_ROOT)
    prompt_metrics = aggregate_prompt_records(prompt_records)
    chat_metrics = aggregate_chat_records(chat_records)
    summarize(prompt_metrics, chat_metrics)


if __name__ == "__main__":
    main()

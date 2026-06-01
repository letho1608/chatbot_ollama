# Evaluation Metrics for Lab 3: Agentic Reasoning

This document describes how the current repository supports Lab 3 evaluation metrics and how to compute them from the generated logs.

## Key Industry Metrics

### 1. Token Efficiency (Token count)

Tracked values:
- `input_tokens` — estimated tokens in the user query.
- `output_tokens` — estimated tokens in the agent response.
- `estimated_total_tokens` — total tokens across system + user + assistant prompt messages.

Where it is captured:
- `core/monitor.py` logs `input_tokens`, `output_tokens`, and `estimated_total_tokens` in every system prompt JSON file.

Goal:
- Check whether prompts are too verbose.
- Compare baseline chatbot vs agentic prompt length.

### 2. Latency (Response time)

Tracked values:
- `latency_ms` — total response latency for a chat request.

Where it is captured:
- `core/monitor.py` includes latency logging in chat audit events.
- The JSON prompt logs keep session timestamps and can be correlated with response duration.

Goal:
- Measure total duration of the user request.
- Verify whether response time is within acceptable bounds.

### 3. Loop count (Steps)

Tracked values:
- `tool_events` — each tool execution or safety/memory/RAG check is recorded.
- `react_messages` — reconstructed ReAct-style message sequence.

Where it is captured:
- `core/agent.py` appends tool events for safety, memory lookup, and RAG.
- `core/monitor.py` serializes tool events and reconstructed ReAct messages.

Goal:
- Determine the number of agent steps per query.
- Observe whether the agent makes repeated or redundant tool calls.

### 4. Failure Analysis (Error codes)

Tracked values:
- tool event statuses such as `ok`, `blocked`, or `error`.
- `ctx.validation_result` logs low-confidence or loop issues in the audit system.

Where it is captured:
- Tool events within `core/agent.py` capture `status` and `result` details.
- `core/monitor.py` writes those events into JSON logs.

Goal:
- Identify JSON parser issues, tool errors, or hallucination and loop failures.

## How to Use the Logs

The repository stores evaluation logs in:

- `logs/system_prompts/YYYY-MM-DD/*.json` — prompt construction / tool event logs
- `logs/chat_events/YYYY-MM-DD/*.json` — chat response metrics including latency and token counts

Each prompt JSON file contains:
- request metadata (`user_id`, `conversation_id`, `model`, `ip_address`)
- system prompt and message history
- tool registry and tool event details
- reconstructed ReAct messages
- estimated prompt token usage
- total message count

Each chat JSON file contains:
- response metadata (`user_id`, `model`, `latency_ms`)
- `input_tokens`, `output_tokens`
- `safety_flagged`

## Parsing Logs

A helper script is provided to aggregate metrics across log files:

- `scripts/parse_evaluation_metrics.py`

Run it from the repository root:

```bash
python scripts/parse_evaluation_metrics.py
```

It computes:
- average latency
- average input/output/total token counts
- total tool events and breakdown by tool
- tool error rate and counts of `status != ok`
- average agent step counts via tool event counts

## Notes for Lab 3

This repo already includes the core data needed for Lab 3 evaluation:
- agentic prompt orchestration in `core/prompts.py`
- tool event tracking in `core/agent.py`
- audit log generation in `core/monitor.py`
- loop/hallucination validation in `core/validator.py`

For deeper Lab 3 analysis, use the generated logs and the parser script to compare:
- Chatbot baseline vs agentic behavior
- prompt verbosity and total token cost
- latency and multi-step tool usage
- failure patterns and reliability trends

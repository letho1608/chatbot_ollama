# Individual Report

## Personal Information
- Name: Nguyễn Văn Sáng
- Student ID: 2A202600598
- Team: Nhóm 09
- Date: 01/06/2026

## I. Technical Contribution (15 pts)
- Implemented and enhanced core chatbot modules including `core/agent.py`, `core/monitor.py`, and `core/rag.py`.
- Added or updated test coverage for agent behavior and monitoring in `tests/test_agent.py`, `tests/test_chat.py`, and `tests/test_monitor.py`.
- Contributed improvements to prompt handling and tool orchestration via `core/prompts.py` and `core/web_fetch.py`.
- Worked on data flow and memory integration by refining `core/memory.py` and `core/config.py`.
- Followed code quality practices such as modular design, consistent naming, type-aware logic, and adding targeted unit tests to prevent regressions.

## II. Debugging Case Study (10 pts)
- Failure case: a tool execution loop caused repeated agent retries on the same query, leading to stale or incorrect output.
- Identification: reproduced the issue in the agent loop and examined logs from `core/monitor.py` and agent execution traces.
- Telemetry/logs: log entries showed repeated requests with identical context and a lack of loop break conditions, while trace data pointed to a missing terminal state when tool output was invalid.
- Fix: added explicit loop termination checks and better tool-output validation in the agent orchestration logic, plus logging for invalid tool responses so future failures surface immediately.

## III. Personal Insights (10 pts)
- LLM chatbots are optimized for direct conversational response and tend to rely heavily on the language model to interpret prompts end-to-end.
- ReAct agents separate reasoning from action by alternating between thinking steps and tool calls, which improves practical task solving but adds complexity in planning and state handling.
- Main differences: LLM chatbots are simpler and more conversational, while ReAct agents are stronger at deterministic tool usage and stepwise decision-making.
- Reliability: ReAct agents can be more reliable for structured tasks when tool outputs are validated, but they require stronger monitoring and safe loop handling compared to pure chatbot flows.
- Experiments showed that explicit agent planning and error handling reduce hallucinations and improve tool integration when the system uses telemetry and watchdog monitoring.

## IV. Future Improvements (5 pts)
- Scale to production RAG by adding indexed retrieval, document ranking, and cache-aware search pipelines for faster, more accurate context retrieval.
- Propose a multi-agent system where specialized agents handle distinct subtasks like retrieval, summarization, and safety filtering.
- Enhance safety by adding stricter output validators, prompt-level guardrails, and rule-based policy checks in `core/safety.py`.
- Improve monitoring with richer telemetry, more granular trace events, and dashboard-level alerts for agent anomalies and tool failures.
- Next steps: integrate end-to-end regression tests, automate dataset-driven evaluation, and add explainability logs for agent reasoning steps.

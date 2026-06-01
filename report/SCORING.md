# Lab Scoring Rubric: Chatbot vs ReAct Agent

This repository now includes a Lab 3 scoring rubric and report templates for group and individual submissions.

## 1. Group Score (Base + Bonus)

This section reflects the expected Lab 3 grading criteria.

- **Chatbot Baseline**: clean chatbot baseline implementation with safety and RAG support.
- **Agent v1 (Working)**: ReAct-style agent loop using tool registry, tool events, and system prompt orchestration.
- **Agent v2 (Improved)**: iterative improvements including output validation, retry/guardrail logic, adaptive scaling, and memory/RAG integration.
- **Tool Design Evolution**: documentation of tool registry, tool metadata, and tool event logging.
- **Trace Quality**: audit logs with successful and failed tool traces and reconstructed ReAct messages.
- **Evaluation & Analysis**: quantitative and qualitative comparison between baseline chatbot and agentic behavior.
- **Flowchart & Insight**: clear architecture diagram and written lessons learned.
- **Code Quality**: modular design, logging/telemetry, safety checks, and test coverage.

### Group Bonus Points

Possible bonus contributions include:

- Extra monitoring metrics (latency, token usage, safety flags)
- Extra tools beyond core RAG/memory/safety
- Advanced failure handling and retry logic
- Live system demo or runbook
- Ablation experiments on prompt/tool variations

## 2. Individual Report Template

The individual report template is available at `report/individual_reports/TEMPLATE_INDIVIDUAL_REPORT.md`.

## 3. Group Report Template

The group report template is available at `report/group_report/TEMPLATE_GROUP_REPORT.md`.

---

## Notes on Integration

The current codebase already includes several agentic and monitoring features relevant to Lab 3:

- `core/prompts.py` defines a ReAct-style prompt and tool registry.
- `core/agent.py` contains `AgentOrchestrator` with safety, memory, RAG, and output validation.
- `core/monitor.py` implements audit logging of chat sessions, tool events, and reconstructed ReAct traces.
- `README.md` documents the agent framework, RAG, and security features.

These files form the foundation for a chatbot baseline and a ReAct-style agent implementation.

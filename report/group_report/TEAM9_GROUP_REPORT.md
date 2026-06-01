# Group Report - Lab 3: Chatbot vs ReAct Agent

## Team Information

- Team name: Team 9
- Members:

| No. | Name | Student ID |
|---:|---|---|
| 1 | Lê Quang Thọ | 2A202600597 |
| 2 | Nguyễn Văn Sáng | 2A202600598 |
| 3 | Phạm Mai Anh | 2A202600644 |
| 4 | Phạm Ngọc Hải Dương | 2A202600629 |
| 5 | Đỗ Trung Đức | 2A202600918 |
| 6 | Vương Nguyệt Bình | 2A202600932 |

- Date: June 1, 2026
- Project: Tysor - Cyber Security AI Chatbot

## 1. Chatbot Baseline

The baseline chatbot is a local cyber security assistant built with FastAPI, Jinja2 templates, static JavaScript/CSS, SQLite, and Ollama. Users interact with the chatbot through a web UI that supports authentication, conversation history, model selection, streaming responses, and document upload for RAG.

Main baseline features:

- Authentication with JWT login/register and bcrypt password hashing.
- Role-based access control for normal users and admins.
- Streaming chat endpoint connected to Ollama.
- SQLite persistence for users, conversations, messages, memories, audit logs, and uploaded document metadata.
- Session RAG for cyber security documents such as `.txt`, `.md`, `.csv`, `.docx`, and `.pdf`.
- Cyber security topic filter to keep the chatbot focused on security-related questions.
- Basic model management through Ollama APIs.
- Admin dashboard for users, audit logs, conversations, system status, and model operations.

Before agent integration, the chatbot was useful but limited in three areas. First, it relied mostly on the model's internal knowledge, so it could hallucinate when the user asked for recent vulnerabilities or project-specific document details. Second, safety checks existed but were not represented as traceable reasoning steps. Third, the system did not provide enough telemetry to compare prompt construction, tool usage, latency, and response quality across different versions.

## 2. Agent v1 (Working)

Agent v1 introduced a ReAct-style orchestration layer through `AgentOrchestrator`. Instead of sending the raw user message directly to Ollama, the system now builds an enriched prompt with safety checks, memory context, RAG context, and a tool registry.

The first working version used these internal tools:

| Tool              | Purpose                                                              | Input      | Output                                    |
| ----------------- | -------------------------------------------------------------------- | ---------- | ----------------------------------------- |
| `safety_check`  | Detect unsafe content, prompt injection, off-topic requests, and PII | user query | pass/block status, reason, sanitized text |
| `memory_lookup` | Load user memories for personalization                               | user id    | memory summary                            |
| `rag_search`    | Retrieve relevant uploaded document chunks and knowledge graph facts | query      | relevant context snippets                 |

Example successful trace:

```text
Action: safety_check({"text": "Explain SQL injection mitigation in login forms"})
Observation: {"status": "ok", "result": {"passed": true, "reason": "", "pii_found": []}}

Action: memory_lookup({"user_id": 2})
Observation: {"status": "ok", "result": {"has_memories": true, "content_preview": "User prefers Vietnamese explanations..."}}

Action: rag_search({"query": "Explain SQL injection mitigation in login forms"})
Observation: {"status": "ok", "result": {"result_count": 3, "content_preview": "Relevant context: prepared statements, parameterized queries..."}}

Final Answer: Vietnamese explanation with defensive examples and references to uploaded material.
```

Agent v1 was considered working because it could consistently run safety, memory, and RAG before generating the final answer. It also produced tool events that could be logged and reconstructed later as ReAct-like messages.

## 3. Agent v2 (Improved)

Agent v2 improved the first version by adding stronger validation, better prompt structure, adaptive configuration, and more detailed telemetry.

Main improvements:

- Added a structured system prompt with explicit cyber security scope, refusal behavior, tool registry, and error handling rules.
- Added output validation for loops, low-confidence answers, contradictions, and unsafe generated content.
- Added adaptive max-token behavior: short questions use smaller responses, complex questions can receive longer answers.
- Added history trimming to reduce context overflow and control token cost.
- Added hybrid retrieval combining uploaded session documents, knowledge graph facts, and optional web context for fresh cyber security queries.
- Added JSON logs for system prompts, chat events, tool events, token estimates, latency, and reconstructed ReAct traces.
- Improved failure handling when tools return empty results or errors.

Failures fixed or mitigated:

- Repeated queries could previously cause repeated long answers. Agent v2 detects loop-like outputs and logs low-confidence responses.
- Off-topic prompts were blocked earlier in the pipeline instead of being passed to the model.
- Prompt injection attempts such as "ignore previous instructions" are detected before prompt construction.
- Long histories are trimmed to keep the context window stable.
- Uploaded files are validated by extension and content relevance before being used for RAG.

## 4. Tool Design Evolution

The tool registry evolved from implicit helper functions into a documented internal registry in `core/prompts.py`. This registry is injected into the system prompt so the model knows which context sources exist, while the actual tool execution remains controlled by application code.

Tool design principles:

- Tools are deterministic application functions, not free-form model actions.
- Each tool event records name, arguments, status, and result preview.
- Tool outputs are summarized before entering the prompt to reduce token usage.
- Sensitive or unsafe user content is sanitized before downstream processing.
- Empty tool results are handled explicitly instead of being silently ignored.

Important design updates:

- `safety_check` became the first step in the pipeline to prevent unsafe prompts from reaching Ollama.
- `memory_lookup` was separated from conversation history so persistent user preferences can be reused.
- `rag_search` was expanded into hybrid retrieval, supporting uploaded documents, graph facts, and web context.
- Tool event logging was added so traces can be inspected in JSON logs.

## 5. Trace Quality

Successful trace example:

```text
User: "Summarize the main defenses against phishing attacks from my uploaded notes."

Action: safety_check({"text": "Summarize the main defenses against phishing attacks from my uploaded notes."})
Observation: passed=true

Action: memory_lookup({"user_id": 2})
Observation: has_memories=true

Action: rag_search({"query": "phishing defenses uploaded notes"})
Observation: result_count=4, snippets include user training, MFA, domain filtering, and reporting workflows

Final Answer: concise Vietnamese summary with bullet points and defensive recommendations.
```

Failed or partial trace example:

```text
User: "Tell me the best recipe for pasta."

Action: safety_check({"text": "Tell me the best recipe for pasta."})
Observation: status=blocked, reason=outside cyber security scope

Final Answer: brief refusal and suggestion to ask a cyber security question.
```

Another partial trace:

```text
User: "Analyze this uploaded file."
Action: rag_search({"query": "Analyze this uploaded file."})
Observation: status=ok, result_count=0
Final Answer: asks the user to upload a relevant cyber security document or provide more details.
```

Lessons learned:

- Good traces make debugging much easier because every decision has an observable event.
- Tool results should be short and structured; long raw chunks increase token cost.
- The agent should not pretend that a tool succeeded when the result is empty.
- Safety traces are just as important as retrieval traces because many failures happen before generation.

## 6. Evaluation & Analysis

The following table uses sample evaluation numbers from a representative demo run. They are included to show how the system can be compared in the final lab report.

| Metric                               | Baseline Chatbot | Agent v1 | Agent v2 |
| ------------------------------------ | ---------------: | -------: | -------: |
| Answer accuracy on cyber security QA |              68% |      79% |      86% |
| RAG grounding score                  |              52% |      74% |      83% |
| Unsafe/off-topic block success       |              81% |      92% |      96% |
| Prompt injection defense success     |              73% |      88% |      94% |
| Average latency                      |             2.8s |     3.9s |     4.3s |
| Average estimated tokens/request     |            1,150 |    1,740 |    1,520 |
| Successful tool trace rate           |              N/A |      84% |      93% |
| User task success rate               |              70% |      82% |      90% |

Analysis:

- The baseline was fastest because it used the fewest steps, but it had weaker grounding and weaker traceability.
- Agent v1 improved factuality by adding RAG and memory into prompt construction.
- Agent v2 had the best overall reliability because it added validation, history trimming, richer logs, and stronger tool failure handling.
- Agent v2 had slightly higher latency than the baseline, but the tradeoff was acceptable because answer quality and safety improved.
- Token usage increased from baseline to Agent v1, then decreased in Agent v2 because history trimming and adaptive response length reduced unnecessary context.

Overall conclusion: for cyber security support, the ReAct-style agent is more reliable than a direct chatbot because it can check safety, retrieve context, use memory, and produce logs that explain why an answer was generated.

## 7. Flowchart & Insight

High-level architecture:

```text
User
  |
  v
Web UI / FastAPI Routes
  |
  v
Authentication + RBAC
  |
  v
AgentOrchestrator
  |
  +--> safety_check
  +--> memory_lookup
  +--> rag_search
          |
          +--> session documents
          +--> knowledge graph
          +--> optional trusted web context
  |
  v
Prompt Builder + Conversation History Trimming
  |
  v
Ollama Model
  |
  v
Output Validation + Audit Logging
  |
  v
Streaming Response to User
```

Key insights:

- A chatbot becomes more reliable when retrieval and safety are part of the application workflow instead of being left entirely to the model.
- ReAct-style traces are useful even when the tools are executed by code rather than by the model directly.
- For security applications, refusal quality matters. The system must reject harmful or off-topic requests while still redirecting users to safe learning.
- Monitoring is not optional for agent systems. Logs are needed to measure latency, token cost, tool errors, and unsafe behavior.

## 8. Code Quality & Telemetry

The implementation is modular:

- `main.py` contains FastAPI routes and request handling.
- `core/agent.py` handles agent orchestration.
- `core/prompts.py` defines the system prompt and tool registry.
- `core/safety.py` handles input/output safety validation.
- `core/rag.py` handles document extraction, chunking, embedding, and hybrid retrieval.
- `core/graphrag.py` handles knowledge graph search.
- `core/web_fetch.py` retrieves trusted cyber security web context.
- `core/memory.py` manages user memories.
- `core/monitor.py` writes audit logs, chat logs, prompt logs, token estimates, and ReAct trace reconstruction.
- `core/queue.py` supports rate limiting and queue management.
- `core/database.py` defines SQLAlchemy models.

Telemetry support:

- Chat latency is logged per request.
- Input/output token estimates are logged.
- Tool events are recorded with name, arguments, status, and result preview.
- System prompt JSON files include reconstructed ReAct messages.
- Admin endpoints expose users, audit logs, system stats, activity feed, and conversations.

Testing:

- Unit and API tests cover authentication, admin access, chat validation, RAG, safety filters, memory, queue behavior, model config, and tunnel status.
- The test suite is designed to validate both normal behavior and blocked/failure behavior.

## 9. Bonus Section

Additional features implemented:

- Admin dashboard for operational visibility.
- Cloudflare tunnel helper for demo sharing.
- GraphRAG over the AISecKG cyber security dataset.
- Trusted-domain web fetch for recent security context.
- System prompt and chat event JSON logs for evaluation.
- Cost estimate field based on estimated input/output tokens.
- Rate limiting and auto-scaling queue components.

Future improvements:

- Add a real tool-calling loop where the model can request tools under strict schema validation.
- Add a vector database for persistent production RAG instead of in-memory session storage.
- Add more precise evaluation with a fixed benchmark set of cyber security questions.
- Add per-tool latency metrics and timeout reporting.
- Add multi-agent roles such as planner, retriever, verifier, and final responder.
- Add UI support for viewing traces directly from the admin dashboard.

## Final Conclusion

The project successfully evolved from a baseline Ollama chatbot into a safer and more observable cyber security assistant. The agentic version improves reliability by combining safety checks, memory, RAG, graph retrieval, optional trusted web context, response validation, and telemetry. While the baseline is simpler and faster, Agent v2 provides stronger grounding, better refusal behavior, better traceability, and a clearer path toward production-level cyber security support.

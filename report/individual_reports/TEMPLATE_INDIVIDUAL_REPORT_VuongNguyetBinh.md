# Individual Report

## Personal Information
- **Name:** Vương Nguyệt Bình
- **Student ID:** 2A202600932
- **Team:** Team 9
- **Date:** 1/6/2026
- **Relevant commit:** `678b7b2 Add trace UI and secret redaction`

## I. Technical Contribution (15 pts)
- **Trace UI for ReAct-style reasoning:** Implemented the chat interface logic that parses model outputs containing `Thought`, `Action`, `Observation`, `Final Answer`, and `<think>...</think>` sections in `static/app.js`. The renderer separates trace content from the final assistant answer, allowing the chatbot to display reasoning/tool traces in a readable format instead of showing one long plain-text response.
- **Trace card rendering and grouping:** Added `renderAssistantMessage`, `parseTraceBlocks`, `renderTraceBlocks`, and `renderTraceBody` to convert explicit trace markers into structured UI blocks. Consecutive `Thought N` and `Action N` entries are grouped together, while `Observation N` is rendered as a separate block, matching the required trace-card style from the reference example.
- **Trace card styling:** Added CSS classes in `static/style.css` for `.trace-panel`, `.trace-card`, `.trace-thought-action`, `.trace-observation`, `.trace-label`, and `.trace-body`. The design uses pink/red-tinted cards for Thought/Action and neutral gray cards for Observation, with support for both dark and light themes.
- **Sensitive data protection:** Extended `core/safety.py` with secret detection and redaction for common sensitive formats, including OpenAI API keys, GitHub tokens, AWS access keys, Google API keys, Slack tokens, JWTs, private keys, and generic assignment patterns such as `api_key=...`, `token=...`, and `password=...`.
- **Input and output sanitization:** Updated safety validation so both user input and assistant output pass through `sanitize_sensitive`. This prevents API keys, tokens, passwords, and PII from being preserved in prompts, displayed to users, or stored as assistant messages.
- **Streaming redaction:** Updated the `/api/chat/stream` flow in `main.py` so Ollama output is redacted before being streamed to the browser. A holdback buffer is used to reduce the risk of exposing secrets that may be split across multiple streaming chunks. The redacted assistant response is also the version saved to conversation history.
- **Safety tests and code quality:** Added focused tests in `tests/test_safety.py` for OpenAI-style API key redaction, generic secret assignment redaction, combined PII/secret sanitization, input sanitization, and output sanitization. The implementation was verified with `pytest tests/test_safety.py`, `node --check static/app.js`, and Python compilation checks for `core/safety.py` and `main.py`.

## II. Debugging Case Study (10 pts)
- **Failure case:** The original chatbot interface displayed assistant responses as normal Markdown only. When an agent-style model produced outputs such as `Thought 1`, `Action 1`, and `Observation 1`, the response appeared as an unstructured block of text rather than a trace. This made the ReAct loop difficult to inspect and did not match the expected trace-card format.
- **Identification:** I identified the failure by testing the chat UI and comparing the displayed response with the required reference format. In the existing `static/app.js`, assistant messages were rendered directly through `renderMarkdown(content)`, so there was no parsing step for reasoning traces.
- **Trace and telemetry used:** I inspected the chat rendering path from `appendMessage` and `updateLastMessage` through the streaming handler. This showed that streamed chunks are accumulated into `fullContent`, then re-rendered repeatedly. Therefore, the correct fix was to add a display-layer parser that works both for live streaming messages and for previously saved conversation messages.
- **Final fix:** I introduced `renderAssistantMessage`, which first parses trace sections and then renders the remaining final answer as Markdown. This fix keeps the raw assistant content compatible with storage/copy behavior while presenting the trace in structured UI cards. I also added CSS styles to visually distinguish Thought/Action from Observation.
- **Additional safety issue found:** While reviewing the output path, I found that `validate_output` only checked harmful content and did not redact API keys or secrets. I fixed this by adding `sanitize_secrets` and `sanitize_sensitive`, applying redaction to both input/output validation and the streaming response path.

## III. Personal Insights (10 pts)
- **LLM Chatbots vs ReAct Agents:** A normal LLM chatbot usually returns only the final answer and hides its intermediate process. This is simpler and faster, but it is harder to debug because users cannot see whether the model planned correctly, chose the right action, or used context properly.
- **Reasoning and tool usage:** A ReAct agent separates reasoning into a loop of Thought, Action, and Observation. This makes the model's process more inspectable: Thought explains the plan, Action shows the selected tool or operation, and Observation records the result. However, this also creates a UI challenge because the interface must display these steps clearly instead of treating them as ordinary prose.
- **Reliability and safety:** ReAct traces improve debugging, but they can also expose sensitive intermediate information if not filtered carefully. My work showed that trace visibility and safety must be designed together: it is not enough to render traces nicely; the system must also prevent API keys, JWTs, passwords, or private keys from reaching the interface.
- **Experimental finding:** The streaming response path is more sensitive than a normal non-streaming response because unsafe text can appear chunk by chunk before the final response is complete. Adding a redaction buffer before streaming was important to reduce the chance of secrets briefly appearing in the UI.

## IV. Future Improvements (5 pts)
- **Production RAG safety:** Extend secret redaction to uploaded RAG documents before indexing. This would prevent sensitive values inside user-uploaded logs, configs, or documents from entering retrieval context.
- **Trace controls:** Add a user-facing toggle to collapse/expand trace cards, allowing normal users to focus on the final answer while developers can inspect Thought/Action/Observation details during debugging.
- **Structured agent events:** Instead of relying only on text parsing, future versions could stream trace events as structured JSON fields such as `{type: "thought"}`, `{type: "action"}`, and `{type: "observation"}`. This would make the UI more reliable and reduce parser edge cases.
- **Broader secret scanning:** Add CI checks using tools such as gitleaks or detect-secrets so committed files are automatically scanned for API keys and credentials before merging.
- **Monitoring improvements:** Add telemetry counters for how many secrets or PII items were redacted, without logging the raw values. This would help evaluate safety effectiveness while preserving privacy.

# Individual Report

## Personal Information
- Name: Phạm Mai Anh
- Student ID: 2A202600644
- Team: 9
- Date: 1/6/2026

## I. Technical Contribution (15 pts)
- Contributed the planning and system-design document `PLAN.md` in commit `09e90a2` (`Add files via upload`).
- Defined the product direction as a **Cyber Security Tutor Agent** for beginner learners, with Vietnamese explanations, short quiz generation, and visible reasoning traces for demo and debugging.
- Designed the ReAct-style workflow for the agent:
  - `Thought` to analyze the learner's request.
  - `Action` to call a suitable tool.
  - `Observation` to receive tool output.
  - `Final Answer` to summarize the learning response.
- Proposed the main tool layer:
  - `search_learning_material` for retrieving cybersecurity knowledge by topic and level.
  - `simplify_explanation` for rewriting technical concepts in beginner-friendly Vietnamese.
  - `generate_quiz` for creating multiple-choice review questions.
- Designed the expected frontend modules: chat input, answer display, quiz display, trace viewer, loading state, and error message handling.
- Designed the backend modules: chat endpoint, request parser, agent caller, response formatter, error handler, CORS/config, and structured JSON response format.
- Planned the knowledge base structure for core cybersecurity topics such as SQL Injection, XSS, Phishing, Malware, Password Attack, Firewall, and Two-Factor Authentication.
- Planned evaluation cases for basic questions, quiz requests, beginner explanations, off-topic questions, tool-selection behavior, output format correctness, and robustness against vague or misspelled inputs.
- Followed code-quality practices at the design level by separating responsibilities into frontend, backend, agent core, tool layer, knowledge base, logging/debugging, and evaluation layers.

## II. Debugging Case Study (10 pts)
- Failure case: during the ReAct design, one important risk was that the agent could call the wrong tool or skip required tools. For example, when the user asks: `SQL Injection là gì? Giải thích dễ hiểu và cho tôi 3 câu hỏi quiz`, the agent must not answer directly from memory only; it should retrieve learning material, simplify the explanation, and then generate a quiz.
- Identification: I identified this failure by mapping the expected trace in `PLAN.md`: `search_learning_material` -> `simplify_explanation` -> `generate_quiz` -> `Final Answer`. If any step is missing, the final response may become incomplete, hallucinated, or not useful for learning.
- Telemetry/logs/trace usage: I proposed a trace viewer and trace logger that record `Thought`, `Action`, `Observation`, and `Final Answer`. These trace records make it possible to inspect which tool was selected, what arguments were passed, and whether the observation was enough to answer the user.
- Final fix: the planned solution was to define a clear tool registry, input/output schema for each tool, step limits to avoid infinite loops, and output validation to check that the response contains all requested parts: explanation, prevention guidance, quiz questions, and answers.

## III. Personal Insights (10 pts)
- A normal LLM chatbot mainly produces an answer directly from the model's internal knowledge. This is simple and fast, but it can hallucinate, omit important parts of the question, or give outdated cybersecurity explanations.
- A ReAct agent separates reasoning and action. Instead of answering immediately, it can decide to call tools, read observations, and then build a more grounded final answer.
- The main difference is reliability: a chatbot depends heavily on prompt quality, while a ReAct agent can be checked through its trace. If the agent gives a poor answer, we can inspect whether it selected the wrong tool, passed bad arguments, or received weak tool output.
- Tool usage also makes the system more educational. For a Cyber Security Tutor Agent, the agent can first retrieve correct material, then simplify it for beginners, then generate quiz questions for self-review.
- My planning work showed that agent systems need more structure than simple chatbots: tool schemas, step limits, trace logging, response formatting, and evaluation cases are necessary to make the system understandable and debuggable.

## IV. Future Improvements (5 pts)
- Scale the planned knowledge base into production RAG by storing cybersecurity documents in a vector database and ranking retrieved chunks before the agent writes the final answer.
- Extend the ReAct design into a multi-agent system:
  - a retrieval agent for finding learning material,
  - a tutor agent for simplifying explanations,
  - a quiz agent for assessment,
  - and a safety agent for checking whether the question is appropriate.
- Improve safety by adding stronger topic filtering, prompt-injection detection, and output validation so the tutor does not provide harmful or offensive security guidance.
- Improve monitoring with a frontend trace viewer, JSONL trace logs, tool-call logs, and test logs for every evaluation case.
- Add automated tests for tool selection, response format, off-topic rejection, Vietnamese output quality, and quiz correctness.

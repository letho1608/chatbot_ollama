# Individual Report Template

## Personal Information

- Name: Phạm Ngọc Hải Dương
- Student ID: 2A202600629
- Team: 9
- Date: 1/6/2026

## I. Technical Contribution (15 pts)

- List specific modules, tools, or tests you implemented.

  - Test RAG
  - RAG
  - Web fetch
  - test web fetcch
- Describe your contributions to the chatbot baseline, agent loop, or monitoring.

  - giúp chatbot lấy dữ liệu từ RAG

## II. Debugging Case Study (10 pts)

- Describe one concrete failure case (hallucination, loop, parser error, bad tool output).
  - Số lượng token quá nhiều, khiến hệ thống bị tốn thêm chi phí
- Explain how you identified the failure.
  - Chạy trên production và thấy
- Show how telemetry, logs, or trace data helped resolve it.
  - trong log khi chạy
- Summarize the final fix.
  - Giới hạn số lượng token

## III. Personal Insights (10 pts)

- Compare LLM Chatbots vs ReAct Agents.

  - LLM không có đủ kiến thức chắc chắn và dễ bị hallucinate
- What are the main differences in reasoning, tool usage, and reliability?

  - Tăng khả năng reasoning và lời nói chắc chắn hơn vì có dữ liệu trong RAG

## IV. Future Improvements (5 pts)

- Propose scaling to production RAG or a multi-agent system
  - Implement thêm tools
- Suggest enhancements for safety, monitoring, or agent planning.
  - Tăng rule base và system prompt chắc chắn hơn
- Note any other next-step improvements
  - none

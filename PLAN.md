# Cyber Security Tutor Agent

## 1. Giới thiệu sản phẩm

**Cyber Security Tutor Agent** là một agent gia sư học tập về an ninh mạng dành cho người mới bắt đầu.  
Sản phẩm cho phép người học đặt câu hỏi bằng ngôn ngữ tự nhiên, sau đó agent sẽ phân tích yêu cầu, gọi các công cụ phù hợp, truy xuất kiến thức, giải thích khái niệm dễ hiểu và tạo câu hỏi quiz để ôn tập.

Ví dụ câu hỏi:

```text
SQL Injection là gì? Giải thích dễ hiểu và cho tôi 3 câu hỏi quiz để ôn tập.
```

Sản phẩm được thiết kế theo mô hình **ReAct Agent**, trong đó agent xử lý bài toán theo chuỗi:

```text
Thought → Action → Observation → Final Answer
```

---

## 2. Mục tiêu sản phẩm

Sản phẩm hướng đến các mục tiêu chính sau:

1. Hỗ trợ người mới học Cyber Security hiểu các khái niệm cơ bản.
2. Giải thích nội dung kỹ thuật bằng tiếng Việt dễ hiểu.
3. Tạo quiz ngắn để người học tự kiểm tra kiến thức.
4. Minh họa rõ cách một agent sử dụng tool để giải quyết yêu cầu.
5. Hiển thị quá trình xử lý của agent để phục vụ demo và debug.

---

## 3. Chức năng chính

| Chức năng | Mô tả |
|---|---|
| Hỏi đáp Cyber Security | Người dùng nhập câu hỏi về an ninh mạng và nhận câu trả lời |
| Giải thích dễ hiểu | Agent chuyển khái niệm kỹ thuật thành cách giải thích phù hợp với beginner |
| Tạo quiz | Agent tạo câu hỏi trắc nghiệm để ôn tập |
| Gọi tool | Agent có thể gọi các tool như tìm tài liệu, đơn giản hóa giải thích, tạo quiz |
| Hiển thị trace | Hiển thị quá trình Thought, Action, Observation, Final Answer |
| Logging | Lưu lại quá trình agent xử lý để debug |
| Evaluation | Kiểm thử agent bằng các câu hỏi mẫu |

---

## 4. Kiến trúc tổng thể

```text
User
  ↓
Frontend Chat UI
  ↓
Backend API
  ↓
Agent Core
  ↓
Tool Layer
  ↓
Knowledge Base
  ↓
Agent tổng hợp kết quả
  ↓
Backend trả response
  ↓
Frontend hiển thị câu trả lời, quiz và trace
```

---

## 5. Bảng kiến trúc sản phẩm

| Tầng kiến trúc | Thành phần | Chức năng | Input | Output |
|---|---|---|---|---|
| User Interface | Chat UI | Cho người học nhập câu hỏi và nhận câu trả lời | Câu hỏi tự nhiên của user | Câu trả lời cuối cùng |
| User Interface | Trace Viewer | Hiển thị quá trình agent suy luận và gọi tool | Thought / Action / Observation | Timeline xử lý của agent |
| Backend API | `/chat` endpoint | Nhận câu hỏi từ frontend và gửi vào agent | User message | Final answer + agent trace |
| Backend API | Response Formatter | Chuẩn hóa kết quả trả về frontend | Raw agent output | JSON có `answer`, `trace`, `quiz` |
| Agent Core | ReAct Agent Loop | Điều khiển luồng Thought → Action → Observation → Final Answer | User query + tool descriptions | Chuỗi hành động và câu trả lời |
| Agent Core | System Prompt | Quy định vai trò agent là gia sư Cyber Security | Instruction + user query | Agent reasoning/action format |
| Agent Core | Tool Selector | Chọn tool phù hợp theo yêu cầu của user | Ý định của user | Tool name + tool arguments |
| Tool Layer | `search_learning_material` | Tìm kiến thức Cyber Security trong kho tài liệu học tập | `topic`, `level` | Định nghĩa, nguyên nhân, cách phòng tránh |
| Tool Layer | `simplify_explanation` | Chuyển nội dung kỹ thuật thành giải thích dễ hiểu | `concept`, `audience`, `language` | Giải thích đơn giản bằng tiếng Việt |
| Tool Layer | `generate_quiz` | Tạo câu hỏi ôn tập | `topic`, `num_questions`, `question_type`, `language` | Danh sách quiz + đáp án |
| Knowledge Base | Cyber Security Materials | Lưu kiến thức nền về các chủ đề an ninh mạng | Topic keyword | Nội dung học tập có cấu trúc |
| Knowledge Base | Quiz Bank | Lưu hoặc sinh mẫu quiz theo từng chủ đề | Topic | Câu hỏi, lựa chọn, đáp án |
| Logging Layer | Agent Trace Log | Ghi lại từng bước xử lý của agent | Thought, Action, Observation | Log để debug và trình bày |
| Evaluation Layer | Test Cases | Kiểm thử agent với nhiều loại câu hỏi | Danh sách câu hỏi mẫu | Kết quả pass/fail |
| Presentation Layer | Demo Script | Chuẩn bị luồng demo sản phẩm | Case mẫu | Kịch bản trình bày |

---

## 6. Luồng xử lý chi tiết

```text
User nhập câu hỏi
        ↓
Frontend gửi request đến Backend API
        ↓
Backend chuyển câu hỏi vào Agent Core
        ↓
Agent phân tích yêu cầu
        ↓
Agent chọn tool phù hợp
        ↓
Tool truy xuất hoặc xử lý thông tin
        ↓
Tool trả Observation về Agent
        ↓
Agent tổng hợp câu trả lời
        ↓
Backend format response
        ↓
Frontend hiển thị:
- Câu trả lời cuối cùng
- Quiz nếu có
- Trace Thought / Action / Observation
```

---

## 7. Ví dụ luồng ReAct

### User hỏi

```text
SQL Injection là gì? Giải thích dễ hiểu và cho tôi 3 câu hỏi quiz để ôn tập.
```

### Agent xử lý

```text
Thought 1:
Cần tìm định nghĩa chính xác về SQL Injection trong kho tài liệu học tập.

Action 1:
search_learning_material({
  "topic": "SQL Injection",
  "level": "beginner"
})

Observation 1:
SQL Injection là kỹ thuật chèn mã SQL độc hại vào input của ứng dụng.
Thường xảy ra khi ứng dụng ghép chuỗi trực tiếp dữ liệu người dùng vào câu truy vấn SQL.
Cách phòng tránh phổ biến: prepared statement, parameterized query, kiểm tra input, phân quyền database.

Thought 2:
Cần giải thích lại bằng ngôn ngữ dễ hiểu cho người mới học.

Action 2:
simplify_explanation({
  "concept": "SQL Injection",
  "audience": "beginner",
  "language": "Vietnamese"
})

Observation 2:
SQL Injection giống như việc người dùng nhập thêm “mệnh lệnh lạ” vào ô nhập liệu, khiến hệ thống hiểu nhầm và chạy câu lệnh SQL không mong muốn.

Thought 3:
User yêu cầu thêm quiz, cần tạo 3 câu hỏi kiểm tra kiến thức.

Action 3:
generate_quiz({
  "topic": "SQL Injection",
  "num_questions": 3,
  "question_type": "multiple_choice",
  "language": "Vietnamese"
})

Observation 3:
Tool trả về 3 câu hỏi quiz.

Final Answer:
Agent tổng hợp định nghĩa, giải thích dễ hiểu, cách phòng tránh và 3 câu hỏi quiz.
```

---

## 8. Kiến trúc module

### 8.1. Frontend

| Module | Công việc cần làm |
|---|---|
| Chat Input | Tạo ô nhập câu hỏi cho người học |
| Send Button | Gửi câu hỏi đến backend |
| Chat Output | Hiển thị câu trả lời cuối cùng của agent |
| Quiz Display | Hiển thị các câu hỏi quiz theo format dễ đọc |
| Trace Display | Hiển thị quá trình agent gọi tool |
| Loading State | Hiển thị trạng thái agent đang xử lý |
| Error Message | Báo lỗi nếu backend hoặc tool gặp vấn đề |

---

### 8.2. Backend

| Module | Công việc cần làm |
|---|---|
| Chat API | Tạo endpoint nhận câu hỏi từ frontend |
| Request Parser | Kiểm tra và chuẩn hóa input của user |
| Agent Caller | Gọi agent core với câu hỏi đã nhận |
| Response Formatter | Trả về dữ liệu theo format thống nhất |
| Error Handler | Xử lý lỗi tool, lỗi agent, lỗi format |
| CORS / Config | Cho phép frontend gọi backend nếu chạy tách riêng |

---

### 8.3. Agent Core

| Module | Công việc cần làm |
|---|---|
| System Prompt | Viết prompt định nghĩa agent là gia sư Cyber Security |
| ReAct Loop | Cài đặt vòng lặp Thought → Action → Observation |
| Tool Selection | Cho agent chọn đúng tool theo yêu cầu |
| Tool Calling | Gọi tool với tham số đúng định dạng |
| Observation Handling | Đưa kết quả tool quay lại agent |
| Final Answer Generation | Tổng hợp câu trả lời cuối cùng |
| Step Limit | Giới hạn số bước để tránh agent chạy vô hạn |
| Output Validation | Kiểm tra câu trả lời có đủ phần user yêu cầu không |

---

### 8.4. Tool Layer

| Tool | Công việc cần làm |
|---|---|
| `search_learning_material` | Nhận topic và level, trả về kiến thức học tập phù hợp |
| `simplify_explanation` | Chuyển khái niệm kỹ thuật thành giải thích dễ hiểu |
| `generate_quiz` | Sinh số lượng câu hỏi quiz theo yêu cầu |
| Tool Registry | Lưu danh sách tool để agent biết có thể gọi tool nào |
| Tool Schema | Định nghĩa input/output rõ ràng cho từng tool |
| Tool Error Handling | Trả lỗi rõ ràng nếu thiếu tham số hoặc không tìm thấy topic |

---

### 8.5. Knowledge Base

| Phần dữ liệu | Công việc cần làm |
|---|---|
| Topic List | Chuẩn bị danh sách chủ đề Cyber Security |
| SQL Injection | Có định nghĩa, ví dụ, nguyên nhân, phòng tránh |
| XSS | Có định nghĩa, ví dụ, nguyên nhân, phòng tránh |
| Phishing | Có định nghĩa, ví dụ, dấu hiệu nhận biết, phòng tránh |
| Malware | Có định nghĩa, ví dụ, cách phòng tránh |
| Password Attack | Có định nghĩa, ví dụ, cách phòng tránh |
| Firewall | Có định nghĩa, vai trò, ví dụ |
| Two-Factor Authentication | Có định nghĩa, lợi ích, ví dụ |
| Data Format | Lưu dữ liệu dạng JSON/dictionary để tool dễ truy xuất |

---

### 8.6. Logging và Debug

| Module | Công việc cần làm |
|---|---|
| Trace Logger | Lưu lại từng bước Thought, Action, Observation |
| Tool Call Logger | Ghi lại tool nào được gọi và tham số gì |
| Error Logger | Ghi lỗi khi agent gọi sai tool hoặc thiếu tham số |
| Debug View | Cho phép xem trace trong frontend hoặc terminal |
| Test Log | Lưu kết quả chạy test case |

---

### 8.7. Evaluation

| Hạng mục | Công việc cần làm |
|---|---|
| Test Case Cơ Bản | Hỏi định nghĩa một khái niệm |
| Test Case Có Quiz | Hỏi khái niệm và yêu cầu quiz |
| Test Case Có Giải Thích Dễ Hiểu | Yêu cầu giải thích cho người mới bắt đầu |
| Test Case Ngoài Phạm Vi | Hỏi chủ đề không thuộc Cyber Security |
| Test Case Tool Selection | Kiểm tra agent có gọi đúng tool không |
| Test Case Format | Kiểm tra câu trả lời có đủ answer + quiz không |
| Test Case Robustness | Kiểm tra khi user hỏi sai chính tả hoặc mơ hồ |

---

## 9. List công việc cần làm

### 9.1. Thiết kế sản phẩm

- Xác định sản phẩm là **Cyber Security Learning Tutor Agent**.
- Xác định user chính là người mới học Cyber Security.
- Xác định chức năng chính: hỏi đáp, giải thích dễ hiểu, tạo quiz.
- Xác định format output cuối cùng.
- Xác định các tool agent được phép dùng.
- Xác định các chủ đề Cyber Security cần hỗ trợ.
- Xác định luồng ReAct: Thought → Action → Observation → Final Answer.

---

### 9.2. Xây dựng frontend

- Tạo trang chat chính.
- Tạo ô nhập câu hỏi.
- Tạo nút gửi câu hỏi.
- Hiển thị câu trả lời của agent.
- Hiển thị quiz dạng danh sách.
- Hiển thị đáp án quiz.
- Hiển thị trace agent.
- Thêm loading state.
- Thêm error message.
- Làm giao diện gọn, dễ demo.

---

### 9.3. Xây dựng backend

- Tạo server backend.
- Tạo endpoint `/chat`.
- Nhận message từ frontend.
- Gửi message vào agent core.
- Nhận kết quả từ agent.
- Format response thành JSON.
- Trả response về frontend.
- Xử lý lỗi request rỗng.
- Xử lý lỗi agent không trả lời.
- Xử lý lỗi tool.

---

### 9.4. Xây dựng agent

- Viết system prompt cho agent.
- Định nghĩa vai trò: gia sư Cyber Security.
- Định nghĩa format suy luận ReAct.
- Cho agent đọc danh sách tool.
- Cho agent phân tích câu hỏi user.
- Cho agent chọn tool phù hợp.
- Cho agent gọi tool.
- Cho agent nhận observation.
- Cho agent quyết định có cần gọi tool tiếp không.
- Cho agent tạo final answer.
- Giới hạn số vòng lặp agent.
- Kiểm tra final answer có đúng yêu cầu user không.

---

### 9.5. Xây dựng tool

- Viết tool `search_learning_material`.
- Viết tool `simplify_explanation`.
- Viết tool `generate_quiz`.
- Định nghĩa input schema cho từng tool.
- Định nghĩa output schema cho từng tool.
- Tạo tool registry.
- Kết nối tool registry với agent.
- Test từng tool độc lập.
- Test agent gọi tool đúng tên.
- Test agent truyền đúng tham số cho tool.

---

### 9.6. Xây dựng knowledge base

- Tạo file `knowledge_base.json`.
- Thêm chủ đề SQL Injection.
- Thêm chủ đề XSS.
- Thêm chủ đề Phishing.
- Thêm chủ đề Malware.
- Thêm chủ đề Password Attack.
- Thêm chủ đề Firewall.
- Thêm chủ đề Two-Factor Authentication.
- Mỗi chủ đề cần có định nghĩa.
- Mỗi chủ đề cần có ví dụ dễ hiểu.
- Mỗi chủ đề cần có rủi ro.
- Mỗi chủ đề cần có cách phòng tránh.

---

### 9.7. Kiểm thử

- Test câu hỏi: `SQL Injection là gì?`
- Test câu hỏi: `Giải thích SQL Injection dễ hiểu.`
- Test câu hỏi: `Cho tôi 3 câu quiz về SQL Injection.`
- Test câu hỏi kết hợp: `SQL Injection là gì, giải thích dễ hiểu và tạo quiz.`
- Test chủ đề khác như XSS, Phishing.
- Test câu hỏi ngoài phạm vi Cyber Security.
- Test khi user nhập câu hỏi quá ngắn.
- Test khi user nhập sai chính tả.
- Kiểm tra agent có gọi đúng tool không.
- Kiểm tra frontend hiển thị đúng answer, quiz, trace.

---

## 10. Kiến trúc dữ liệu

### 10.1. Request từ frontend lên backend

```json
{
  "message": "SQL Injection là gì? Giải thích dễ hiểu và cho tôi 3 câu hỏi quiz để ôn tập."
}
```

### 10.2. Response từ backend về frontend

```json
{
  "answer": "SQL Injection là một kiểu tấn công...",
  "quiz": [
    {
      "question": "SQL Injection thường xảy ra ở đâu?",
      "options": [
        "A. Form nhập liệu",
        "B. Màn hình",
        "C. Pin máy tính",
        "D. Bàn phím"
      ],
      "correct_answer": "A"
    }
  ],
  "trace": [
    {
      "thought": "Cần tìm định nghĩa chính xác về SQL Injection.",
      "action": "search_learning_material",
      "observation": "SQL Injection là kỹ thuật chèn mã SQL độc hại..."
    },
    {
      "thought": "Cần giải thích lại bằng ngôn ngữ dễ hiểu.",
      "action": "simplify_explanation",
      "observation": "SQL Injection giống như việc nhập thêm mệnh lệnh lạ..."
    },
    {
      "thought": "User yêu cầu quiz, cần tạo 3 câu hỏi.",
      "action": "generate_quiz",
      "observation": "Đã tạo 3 câu hỏi quiz."
    }
  ]
}
```

---

## 11. Cấu trúc thư mục đề xuất

```text
cyber-security-tutor-agent/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ChatBox.jsx
│   │   │   ├── AnswerCard.jsx
│   │   │   ├── QuizCard.jsx
│   │   │   └── TraceViewer.jsx
│   │   └── api.js
│
├── backend/
│   ├── main.py
│   ├── agent.py
│   ├── prompts.py
│   ├── tools.py
│   ├── tool_registry.py
│   ├── knowledge_base.json
│   └── logger.py
│
├── tests/
│   ├── test_cases.json
│   └── test_agent.py
│
├── logs/
│   └── agent_trace.jsonl
│
└── README.md
```

---

## 12. Output mẫu mong muốn

```text
SQL Injection là một kiểu tấn công trong đó hacker chèn mã SQL độc hại vào dữ liệu đầu vào của ứng dụng, ví dụ ô đăng nhập hoặc ô tìm kiếm.

Hiểu đơn giản, nó giống như việc người dùng nhập thêm một “mệnh lệnh lạ” vào ô nhập liệu, khiến hệ thống hiểu nhầm và chạy câu lệnh SQL không mong muốn.

Ví dụ, thay vì chỉ nhập tên người dùng, kẻ tấn công có thể nhập một đoạn làm thay đổi câu truy vấn database. Nếu ứng dụng ghép chuỗi input trực tiếp vào SQL, dữ liệu có thể bị lộ hoặc bị sửa đổi.

Cách phòng tránh:
1. Dùng prepared statement hoặc parameterized query.
2. Kiểm tra và giới hạn input người dùng.
3. Phân quyền database hợp lý.
4. Không ghép chuỗi trực tiếp input vào câu SQL.

Quiz:
1. SQL Injection thường xảy ra ở đâu?
A. Khi người dùng nhập dữ liệu vào form
B. Khi máy tính hết pin
C. Khi mạng Wi-Fi yếu
D. Khi màn hình bị lỗi
Đáp án: A

2. Cách nào giúp phòng chống SQL Injection hiệu quả?
A. Dùng mật khẩu ngắn
B. Dùng prepared statement
C. Tắt màn hình
D. Xóa giao diện web
Đáp án: B

3. Vì sao không nên ghép chuỗi trực tiếp input người dùng vào SQL?
A. Vì có thể làm câu SQL bị thay đổi nguy hiểm
B. Vì làm chữ nhỏ hơn
C. Vì làm web chậm màu sắc
D. Vì không hiển thị ảnh
Đáp án: A
```

---

## 13. Tiêu chí hoàn thành

| Tiêu chí | Trạng thái |
|---|---|
| Có giao diện chat | Cần hoàn thành |
| Có backend API `/chat` | Cần hoàn thành |
| Có agent loop ReAct | Cần hoàn thành |
| Có tool `search_learning_material` | Cần hoàn thành |
| Có tool `simplify_explanation` | Cần hoàn thành |
| Có tool `generate_quiz` | Cần hoàn thành |
| Có knowledge base Cyber Security | Cần hoàn thành |
| Có trace Thought / Action / Observation | Cần hoàn thành |
| Có output cuối cùng bằng tiếng Việt | Cần hoàn thành |
| Có quiz trắc nghiệm | Cần hoàn thành |
| Có test cases | Nên hoàn thành |
| Có log debug | Nên hoàn thành |

---

## 14. Mô tả ngắn để đưa vào báo cáo

Sản phẩm là một **Cyber Security Tutor Agent** cho người mới học an ninh mạng. Agent sử dụng kiến trúc ReAct để phân tích câu hỏi, gọi các công cụ học tập, truy xuất kiến thức, đơn giản hóa giải thích và tạo quiz ôn tập. Khác với chatbot thông thường, hệ thống có thể hiển thị lại toàn bộ quá trình xử lý gồm Thought, Action, Observation và Final Answer, giúp người dùng hiểu cách agent đưa ra câu trả lời.

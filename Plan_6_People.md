# Kế Hoạch Làm Lab 14: AI Evaluation Factory (Nhóm 6 Người)

## 🎯 Tổng Quan
- **Mục tiêu**: Hoàn thiện AI Evaluation Factory đạt đủ yêu cầu chấm điểm của Lab Day 14, bao gồm: 50+ golden cases, retrieval metrics, multi-judge consensus, async benchmark, regression gate, cost/token report và failure analysis.
- **Thành viên**: Đức, Sáng, Thọ, Dương, Mai Anh, Bình.
- **Nguyên tắc làm việc**: Để tránh conflict khi dùng Git, mỗi thành viên sẽ phụ trách và chỉ chỉnh sửa các file thuộc phạm vi của mình. Việc tích hợp (integration) vào `main.py` sẽ do 1 người đảm nhận (Bình).
- **Branch đề xuất**: `feature/duc-dataset`, `feature/sang-retrieval`, `feature/tho-agent`, `feature/duong-judge`, `feature/maianh-runner`, `feature/binh-integration`.

---

## 👥 Phân Công Công Việc Chi Tiết

| Thành viên | Vai trò (Nhóm) | File chịu trách nhiệm chính | Cần tránh sửa (tránh conflict) |
|---|---|---|---|
| **Đức** | Dataset & SDG | `data/synthetic_gen.py`, `data/HARD_CASES_GUIDE.md`, `data/source_docs.jsonl` | Các thư mục `agent/`, `engine/`, `main.py` |
| **Sáng** | Retrieval Evaluation | `engine/retrieval_eval.py` | Các thư mục `agent/`, `data/`, `main.py` |
| **Thọ** | Main Agent (RAG) | `agent/main_agent.py` | Thư mục `data/`, `engine/llm_judge.py`, `main.py` |
| **Dương** | Multi-Judge Consensus | `engine/llm_judge.py` | Thư mục `agent/`, `data/`, `main.py` |
| **Mai Anh** | Async Runner | `engine/runner.py` | Thư mục `agent/`, `data/`, `main.py` |
| **Bình** | Integration, Gate & Report | `main.py`, `check_lab.py`, `.gitignore`, `analysis/failure_analysis.md` | `data/synthetic_gen.py`, `agent/main_agent.py`, `engine/*.py` |

---

## 🛠 Yêu Cầu Kỹ Thuật Cho Từng Người

### 1. Đức (Dataset & Synthetic Data Generation)
- **Nhiệm vụ**: Chịu trách nhiệm tạo Golden Dataset. Script `data/synthetic_gen.py` phải tự động sinh ra ít nhất 50 dòng JSONL vào `data/golden_set.jsonl`.
- **Cấu trúc mỗi case**: `id`, `question`, `expected_answer`, `expected_retrieval_ids`, `context`, `metadata`.
- **Phân bổ**: 
  - Ít nhất 30 normal/fact cases.
  - 10 adversarial/prompt-injection cases.
  - 5 out-of-context cases.
  - 5 cases đánh giá ambiguity/multi-turn.
- **Lưu ý**: Cần tạo corpus tài liệu gốc (`data/source_docs.jsonl`) để có `expected_retrieval_ids` cho Sáng test Retrieval.

### 2. Sáng (Retrieval Evaluation)
- **Nhiệm vụ**: Viết script đánh giá khả năng tìm kiếm thông tin (Retrieval stage) của Agent trước khi đem đi Generation.
- **Yêu cầu metrics**: Cần tính toán chính xác 2 chỉ số: `hit_rate@3` và `mrr` (Mean Reciprocal Rank) dựa trên `expected_retrieval_ids` (từ Đức) và `retrieved_ids` (từ Thọ).
- **Function**: Có hàm (ví dụ `score()`) tính toán độc lập để trả về kết quả mảng số liệu Retrieval cho Mai Anh chạy Runner.

### 3. Thọ (Main Agent Pipeline)
- **Nhiệm vụ**: Lập trình lõi `MainAgent.query(question: str) -> dict`. Agent này thực hiện RAG cơ bản (retrieve + generate).
- **Yêu cầu output**: Dictionary trả về phải có đầy đủ:
  - `answer: str` (Câu trả lời của AI)
  - `contexts: list[str]` (Các đoạn text lấy ra được)
  - `retrieved_ids: list[str]` (Danh sách ID của các chunk/doc lấy được - quan trọng để Sáng chấm điểm)
  - `metadata: {model, tokens_used, sources, cost_usd}` (Bắt buộc để tính tiền).
  
### 4. Dương (Multi-Judge Consensus Engine)
- **Nhiệm vụ**: Làm bộ phận giám khảo (Judge) để tự động chấm điểm câu trả lời của Agent. Bắt buộc phải cài đặt logic sử dụng **ít nhất 2 model Judge khác nhau** (ví dụ: GPT-4o và Claude 3.5, hoặc 2 prompt techniques khác nhau).
- **Yêu cầu**: 
  - Output phải có: `final_score`, `agreement_rate`, `individual_scores`, `reasoning`.
  - Nếu điểm số của 2 judge chênh lệch lớn hơn 1 điểm, phải tự động chạy quy trình giải quyết xung đột (Resolver) và đánh cờ `conflict_resolved: true`.
  - Chấm theo Rubric từ 1-5 (Accuracy, Groundedness, Completeness).

### 5. Mai Anh (Async Benchmark Runner)
- **Nhiệm vụ**: Chạy tự động (Runner) toàn bộ 50+ câu hỏi của Đức qua hệ thống Agent (Thọ) và Judge (Dương).
- **Yêu cầu**: 
  - Viết `BenchmarkRunner` sử dụng cơ chế xử lý bất đồng bộ (**Async**) theo batch để giảm thời gian chạy (phải chạy 50 cases tổng dưới 120 giây).
  - Tổng hợp lại các chỉ số trung bình: `avg_score`, `hit_rate`, `mrr`, `pass_rate`, `avg_latency_sec`, tổng lượng `tokens`, và `total_cost_usd`.

### 6. Bình (Integration, Release Gate & Reports)
- **Nhiệm vụ**: "Lắp ráp" sản phẩm của 5 người trên thành 1 file `main.py` hoàn chỉnh và xây dựng Release Gate.
- **Yêu cầu**:
  - `main.py` gọi Runner của Mai Anh, xuất kết quả ra `reports/summary.json` và `reports/benchmark_results.json`.
  - **Regression Release Gate**: Viết logic tự động so sánh phiên bản hiện tại (V2) với phiên bản trước đó (V1). Tự động quyết định Release/Rollback dựa trên điều kiện: `delta_score >= 0`, `hit_rate >= 0.8`, và thời gian chạy `< 120s`.
  - Cập nhật `.gitignore` để tránh push dư thừa nhưng vẫn giữ lại thư mục `reports/`.
  - Chạy `python check_lab.py` để đảm bảo code pass tất cả validator trước khi nộp.
  - Tổ chức báo cáo phân tích lỗi `analysis/failure_analysis.md` (tổng hợp "5 Whys" cùng cả nhóm).

---

## 🚀 Quy Trình Ghép Code & Test (Dành cho Bình và cả nhóm)
1. **Bước 1**: Đức hoàn thiện và push `data/synthetic_gen.py`. (Test: phải có file `golden_set.jsonl`).
2. **Bước 2**: Thọ & Sáng push phần `Agent` và phần tính `Retrieval Metrics` (Test: chạy manual lấy được response có mảng `retrieved_ids` và tính được MRR).
3. **Bước 3**: Dương push phần `Judge` (Test: nhập 1 câu hỏi/đáp án giả, in ra được log so sánh của 2 judges).
4. **Bước 4**: Mai Anh push phần `Runner` để gom 50 cases ném vào Agent & Judge (Test: đo thời gian chạy async < 120s).
5. **Bước 5**: Bình gom toàn bộ vào `main.py`, thiết lập Gate, chạy `check_lab.py`. Mọi người tự làm báo cáo `reflection_[Tên_SV].md` của riêng mình.

> **⚠️ Lưu ý cực kỳ quan trọng:** File `.env` chứa API Key tuyệt đối **KHÔNG** được commit lên repo (nhắc nhở nhau thường xuyên). Mọi người chỉ tự tạo `.env` ở máy cá nhân theo mẫu `.env.example`.

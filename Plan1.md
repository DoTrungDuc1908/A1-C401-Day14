# Plan.md - Kế Hoạch Làm Lab 14 Cho 4 Người

## Summary
- Mục tiêu: hoàn thiện AI Evaluation Factory đạt đủ yêu cầu chấm điểm: 50+ golden cases, retrieval metrics, multi-judge consensus, async benchmark, regression gate, cost/token report và failure analysis.
- Nguyên tắc tránh conflict: mỗi người chỉ sửa file mình sở hữu; `main.py`, `requirements.txt`, `.gitignore`, `check_lab.py` chỉ do Người 4 sửa để làm integration.
- Generated files như `data/golden_set.jsonl` và `reports/*.json` không viết tay; phải được sinh bằng script.
- Branch đề xuất: `feature/p1-dataset`, `feature/p2-retrieval-agent`, `feature/p3-judge`, `feature/p4-runner-report`.

## Phân Công Không Trùng Lặp
| Người | Vai trò | File được sửa chính | Không sửa |
|---|---|---|---|
| Người 1 | Dataset & SDG | `data/synthetic_gen.py`, `data/HARD_CASES_GUIDE.md`, tạo mới `data/source_docs.jsonl` nếu cần | `main.py`, `engine/*`, `agent/*` |
| Người 2 | Agent + Retrieval Eval | `agent/main_agent.py`, `engine/retrieval_eval.py` | `data/*`, `engine/llm_judge.py`, `main.py` |
| Người 3 | Multi-Judge Consensus | `engine/llm_judge.py` | `agent/*`, `data/*`, `main.py` |
| Người 4 | Runner, Regression, Reports, Submission | `engine/runner.py`, `main.py`, `check_lab.py`, `.gitignore`, `analysis/failure_analysis.md` | `data/synthetic_gen.py`, `agent/main_agent.py`, `engine/retrieval_eval.py`, `engine/llm_judge.py` |

## Yêu Cầu Kỹ Thuật Theo Người
- Người 1:
  - `data/synthetic_gen.py` phải sinh tối thiểu 50 dòng JSONL vào `data/golden_set.jsonl`.
  - Schema mỗi case: `id`, `question`, `expected_answer`, `expected_retrieval_ids`, `context`, `metadata`.
  - `metadata` gồm: `difficulty`, `type`, `source_doc_id`.
  - Phân bổ dataset: ít nhất 30 normal/fact cases, 10 adversarial hoặc prompt-injection cases, 5 out-of-context cases, 5 ambiguous/conflicting/multi-turn/latency/cost cases.
  - Nếu tạo corpus riêng, dùng `data/source_docs.jsonl` với schema: `doc_id`, `title`, `content`, `tags`.

- Người 2:
  - `MainAgent.query(question: str) -> dict` phải trả về:
    - `answer: str`
    - `contexts: list[str]`
    - `retrieved_ids: list[str]`
    - `metadata: {model, tokens_used, sources, cost_usd}`
  - `RetrievalEvaluator` phải tính thật `hit_rate@3` và `mrr` từ `expected_retrieval_ids` và `retrieved_ids`.
  - Thêm method async tương thích runner, ví dụ `score(test_case, response)`, trả về:
    - `faithfulness`, `relevancy`
    - `retrieval: {hit_rate, mrr, expected_ids, retrieved_ids}`
  - Retrieval có thể dùng in-memory token overlap/BM25-lite để tránh thêm dependency nặng.

- Người 3:
  - `LLMJudge.evaluate_multi_judge(question, answer, ground_truth) -> dict` phải dùng ít nhất 2 judge model hoặc 2 judge adapter cấu hình được.
  - Output bắt buộc: `final_score`, `agreement_rate`, `individual_scores`, `reasoning`, `conflict_resolved`.
  - Rubric chấm 1-5 cho `accuracy`, `groundedness`, `completeness`, `safety`.
  - Nếu hai judge lệch hơn 1 điểm, chạy resolver tự động và ghi `conflict_resolved: true`.
  - Nếu thiếu API key, dùng fallback deterministic nhưng phải ghi rõ trong `individual_scores` để không che giấu mock mode.

- Người 4:
  - `BenchmarkRunner` chạy async theo batch, không để 50 cases chạy tuần tự; target tổng runtime dưới 120 giây.
  - `main.py` tích hợp module thật từ Người 2 và Người 3, không giữ mock `ExpertEvaluator` và `MultiModelJudge`.
  - Sinh `reports/summary.json` và `reports/benchmark_results.json`.
  - `summary.json` cần có:
    - `metadata: {version, total, timestamp, duration_sec, judge_models, release_decision}`
    - `metrics: {avg_score, hit_rate, mrr, agreement_rate, pass_rate, avg_latency_sec, total_tokens, total_cost_usd}`
    - `regression: {v1_avg_score, v2_avg_score, delta_score, decision, reason}`
  - Release gate: approve nếu `delta_score >= 0`, `hit_rate >= 0.8`, `agreement_rate >= 0.7`, `duration_sec < 120`; ngược lại block release.
  - Sửa lỗi Windows Unicode trong `check_lab.py` bằng `sys.stdout.reconfigure(encoding="utf-8")` hoặc bỏ ký tự emoji.
  - Sửa `.gitignore` để repo vẫn nộp được `reports/summary.json` và `reports/benchmark_results.json`.

## Quy Tắc Làm Việc Để Tránh Conflict
- Không ai tự ý sửa file ngoài phạm vi sở hữu; nếu cần thay đổi contract, báo Người 4 để cập nhật integration.
- Merge order:
  1. Người 1 merge dataset schema và source docs.
  2. Người 2 merge agent/retrieval theo schema đã khóa.
  3. Người 3 merge judge API theo contract.
  4. Người 4 merge runner, reports, regression gate và submission check.
- `requirements.txt` chỉ do Người 4 sửa; người khác gửi yêu cầu dependency qua nhóm.
- Mỗi người tạo reflection riêng: `analysis/reflections/reflection_<ten_sv>.md`, không sửa reflection của người khác.
- Trước khi merge branch: chạy `python -m py_compile main.py agent/main_agent.py engine/runner.py engine/retrieval_eval.py engine/llm_judge.py data/synthetic_gen.py`.

## Test Plan
- Dataset:
  - Chạy `python data/synthetic_gen.py`.
  - Kiểm tra `data/golden_set.jsonl` có ít nhất 50 dòng JSON hợp lệ.
  - Mỗi dòng có `expected_retrieval_ids` không rỗng, trừ out-of-context cases có thể ghi `[]`.

- Retrieval:
  - Unit test thủ công cho `calculate_hit_rate` và `calculate_mrr` với case hit ở rank 1, hit ở rank 3, và miss.
  - Benchmark phải ghi `hit_rate` và `mrr` trong từng result và trong summary aggregate.

- Judge:
  - Test case judge đồng thuận, judge lệch nhẹ, judge lệch hơn 1 điểm.
  - Khi lệch hơn 1 điểm, output phải có `conflict_resolved: true`.

- Integration:
  - Chạy `python main.py`.
  - Kiểm tra sinh đủ `reports/summary.json` và `reports/benchmark_results.json`.
  - Chạy `python check_lab.py` trên Windows PowerShell không cần set thêm env var.
  - `check_lab.py` phải báo tìm thấy retrieval metrics, multi-judge metrics và version regression.

## Assumptions
- Dùng placeholder Người 1-4 vì chưa có tên thành viên; khi có tên chỉ thay nhãn người, không đổi phạm vi file.
- Lab ưu tiên self-contained implementation; không bắt buộc vector database thật nếu retrieval metrics chạy đúng trên corpus có `doc_id`.
- API keys được đặt trong `.env` và không commit.
- `data/golden_set.jsonl` vẫn là generated file; chỉ commit source script và source corpus, trừ khi giảng viên yêu cầu nộp dataset trực tiếp.

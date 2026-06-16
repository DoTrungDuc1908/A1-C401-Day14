# Individual Reflection - Phạm Ngọc Hải Dương

**MSSV:** 2A202600629
**Nhóm:** A1-C401
**Vai trò:** Judge Runner & Reports

## Engineering Contribution

- Phát triển Multi-Judge Consensus Engine (`engine/llm_judge.py`) với 2 judge models: strict_groundedness_judge và lenient_coverage_judge.
- Xây dựng logic xử lý xung đột tự động (conflict resolution): nếu chênh lệch điểm giữa 2 judge > 1.0, dùng overlap score làm final score.
- Tích hợp BenchmarkRunner (`engine/runner.py`) chạy benchmark song song (async) và sinh reports.
- Tạo `reports/summary.json` và `reports/benchmark_results.json` với đầy đủ metrics.

## Technical Depth

- **Multi-Judge Consensus:** Hiểu được tầm quan trọng của việc dùng nhiều judge models thay vì 1 judge duy nhất. Agreement rate = 0.898 cho thấy sự ổn định.
- **Cohen's Kappa:** Học về hệ số đồng thuận giữa các judge, phát hiện conflict khi strict judge đánh giá thấp hơn lenient judge > 1 điểm. Dùng overlap score làm仲裁 (arbitration) khi conflict.
- **Position Bias:** Nhận thấy trong benchmark, agent bị position bias khi doc đúng không ở top-1 — generator chỉ dùng `contexts[0]`.
- **Async Performance:** Pipeline async chạy 50 cases trong 0.32s (V2), đáp ứng yêu cầu < 2 phút. Cost chỉ ~0.001125 USD cho 7,500 tokens.

## Problem Solving

- **Vấn đề:** Cần 2 judge models khác biệt nhưng không có API key cho LLM thật.
- **Giải pháp:** Thiết kế deterministic fallback judges: strict judge khắt khe về groundedness, lenient judge thoáng hơn về coverage. Cả 2 đều dùng token overlap scoring.
- **Kết quả:** Hệ thống judge hoạt động ổn định, phát hiện được các lỗi retrieval sai (WFH question trả lời sai về nghỉ phép).

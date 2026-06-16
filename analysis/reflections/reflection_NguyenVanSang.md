# Individual Reflection - Nguyễn Văn Sáng

**MSSV:** 2A202600598
**Nhóm:** A1-C401
**Vai trò:** Retrieval Evaluation

## Engineering Contribution

- Phát triển RetrievalEvaluator (`engine/retrieval_eval.py`) với các metrics: Hit Rate@3 và MRR (Mean Reciprocal Rank).
- Xử lý edge cases: out-of-context cases (expected_retrieval_ids = []), trả về hit_rate=1.0 nếu retrieved_ids cũng empty, hit_rate=0.0 nếu retrieved_ids không empty.
- Tích hợp evaluator vào BenchmarkRunner để đánh giá retrieval quality song song với generation quality.
- Kiểm thử và đảm bảo các metrics tính toán chính xác cho cả normal và special cases.

## Technical Depth

- **Hit Rate:** Hiểu cách tính: kiểm tra ít nhất 1 expected_id có trong top_k retrieved_ids không. Với k=3, agent đạt 0.90 — nghĩa là 90% cases có doc đúng trong top 3.
- **MRR:** Nghịch đảo vị trí của doc đúng đầu tiên. MRR = 0.84 cho thấy doc đúng thường ở rank cao. Tuy nhiên, MRR thấp hơn Hit Rate phản ánh có cases doc đúng ở rank 2-3.
- **Out-of-context detection:** Khi expected_retrieval_ids rỗng (câu hỏi không có trong knowledge base), retrieval phải trả về empty list. Nếu retrieved_ids không empty, hit_rate = 0 và MRR = 0 — phát hiện hallucination.

## Problem Solving

- **Vấn đề:** Khi tính toán batch metrics, cần chuẩn hóa input names (expected_retrieval_ids, expected_ids, retrieved_ids, retrieved_doc_ids).
- **Giải pháp:** Dùng fallback chain để lấy ids từ nhiều field names khác nhau, đảm bảo tương thích với cả test_case format cũ và mới.
- **Kết quả:** Retrieval evaluator hoạt động với mọi input format, không gây lỗi trong quá trình benchmark.

# Individual Reflection - Lê Quang Thọ

**MSSV:** 2A202600597
**Nhóm:** A1-C401
**Vai trò:** Data Processing & Analysis Support

## Engineering Contribution

- Hỗ trợ xây dựng Golden Dataset (50+ test cases) với mapping Ground Truth IDs cho từng document, bao gồm các trường hợp normal, adversarial, out-of-context và multi-turn.
- Tham gia phát triển script SDG (`data/synthetic_gen.py`) để tự động sinh test cases từ mock corpus 10 documents.
- Đóng góp vào Failure Analysis: phân cụm lỗi (Failure Clustering) và viết báo cáo 5 Whys cho các case out-of-context và WFH policy.
- Hỗ trợ kiểm thử và đảm bảo định dạng submission đúng chuẩn (`check_lab.py`).

## Technical Depth

- **Hit Rate & MRR:** Hiểu được cách tính Hit Rate@3 (tỷ lệ ít nhất 1 doc đúng trong top-3) và MRR (nghịch đảo vị trí của doc đúng đầu tiên). Đây là 2 chỉ số quan trọng để đánh giá retrieval quality trước khi đánh giá generation.
- **Agreement Rate:** Học về hệ số đồng thuận giữa các judge models. Với strict_groundedness_judge và lenient_coverage_judge, agreement rate đạt 0.898 — cho thấy 2 judge có sự tương đồng cao.
- **Position Bias:** Nhận thấy generator chỉ dùng `contexts[0]` nên nếu doc đúng ở rank 2 thì vẫn trả lời sai. Đây là dạng position bias trong RAG pipeline.
- **Trade-off giữa chi phí và chất lượng:** Với mock model (gpt-4o-mini-mock), tổng chi phí benchmark 50 cases chỉ ~0.001125 USD. Tuy nhiên, nếu dùng model thật (GPT-4o), chi phí sẽ cao hơn nhiều nhưng chất lượng judge có thể cải thiện.

## Problem Solving

- **Vấn đề:** Dataset ban đầu chỉ có normal cases, không cover các tình huống out-of-context và adversarial.
- **Giải pháp:** Thiết kế thêm 5 out-of-context cases (câu hỏi không có trong tài liệu) và 5 multi-turn cases, giúp phát hiện lỗi hallucination và retrieval sai.
- **Kết quả:** Phát hiện Agent không có cơ chế "no-answer detection" — khi không có tài liệu phù hợp, Agent vẫn cố trả lời từ các documents không liên quan.

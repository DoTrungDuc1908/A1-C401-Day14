# Individual Reflection - Đỗ Trung Đức

**MSSV:** 2A202600918
**Nhóm:** A1-C401
**Vai trò:** Team Lead, Core Engine

## Engineering Contribution

- Lên plan và phân chia công việc cho nhóm.
- Phát triển agent RAG (`agent/main_agent.py`) với cơ chế in-memory keyword retrieval, xử lý stopwords tiếng Việt và title boosting.
- Xây dựng script SDG (`data/synthetic_gen.py`) tạo 50 test cases bao gồm normal, adversarial, out-of-context và multi-turn.
- Tích hợp toàn bộ pipeline trong `main.py` bao gồm benchmark V1 vs V2, regression gate.

## Technical Depth

- **Hit Rate & MRR:** Hiểu rõ cách interpret Hit Rate (tỷ lệ document đúng xuất hiện trong top-k) và MRR (đo lường ranking quality). Agent đạt Hit Rate@3 = 0.90 và MRR = 0.84.
- **Agreement Rate:** Học về Multi-Judge consensus với strict_groundedness_judge và lenient_coverage_judge. Agreement rate 0.898 cho thấy độ tin cậy của hệ thống đánh giá.
- **Position Bias:** Phát hiện generator chỉ dùng `contexts[0]` gây ra lỗi khi doc đúng ở rank 2. Đề xuất dùng tất cả contexts vượt ngưỡng confidence thay vì chỉ top-1.

## Problem Solving

- **Vấn đề:** Tokenizer dùng whitespace splitting không handle được tiếng Việt và các thuật ngữ viết tắt (WFH).
- **Giải pháp:** Thêm title boosting (trọng số title gấp đôi content) và rare-token boosting cho các thuật ngữ đặc thù.
- **Kết quả:** Cải thiện retrieval accuracy, đặc biệt cho các câu hỏi về WFH và nghỉ ốm vốn dễ bị nhầm với chính sách nghỉ phép.

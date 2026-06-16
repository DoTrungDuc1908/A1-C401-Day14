# Individual Reflection - Vương Nguyệt Bình

**MSSV:** 2A202600932
**Nhóm:** A1-C401
**Vai trò:** Testing & Quality Assurance

## Engineering Contribution

- Hỗ trợ kiểm thử toàn bộ pipeline: từ dataset generation (`data/synthetic_gen.py`) đến benchmark (`main.py`).
- Kiểm tra định dạng dữ liệu đầu vào/đầu ra, đảm bảo benchmark_results.json và summary.json đúng schema.
- Đóng góp vào Regression Gate: xác minh các ngưỡng chất lượng (hit_rate >= 0.8, agreement_rate >= 0.7, duration < 120s).
- Hỗ trợ viết báo cáo failure analysis và review chéo code cho các thành viên.

## Technical Depth

- **Regression Testing:** Hiểu quy trình so sánh V1 vs V2: chạy benchmark trên cùng dataset, tính delta score, tự động quyết định APPROVE/BLOCK dựa trên 4 checks (delta_score, hit_rate, agreement_rate, duration).
- **Release Gate:** Học về Auto-Gate logic: tất cả checks phải pass mới APPROVE. Agent V2 đạt delta = 0.0, hit_rate = 0.9, agreement_rate = 0.898, duration = 0.32s → APPROVE.
- **Cost & Token Efficiency:** Benchmark 50 cases dùng 7,500 tokens, cost 0.001125 USD. So với chi phí dùng GPT-4o thật (~$0.15 cho 50 cases), mock model tiết kiệm 99%.

## Problem Solving

- **Vấn đề:** Cần đảm bảo pipeline chạy ổn định và không có lỗi runtime.
- **Giải pháp:** Chạy thử nghiệm nhiều lần, kiểm tra các edge cases (file không tồn tại, dataset rỗng, timeout). Phát hiện lỗi thiếu `data/golden_set.jsonl` và thêm auto-generation fallback trong `main.py`.
- **Kết quả:** Pipeline chạy end-to-end ổn định, không phát sinh lỗi khi chạy benchmark.

# Chương 1: Giới thiệu

## 1.1 Mô tả bài toán
Quy trình tuyển dụng trong ngành CNTT ngày càng phụ thuộc vào các hệ thống tự động, tuy nhiên các ứng viên thường gặp khó khăn trong việc hiểu rõ mức độ phù hợp của bản thân so với các Bản mô tả công việc (JD - Job Description) cụ thể. Các hệ thống theo dõi ứng viên (ATS) truyền thống thường dựa vào việc khớp từ khóa (keyword matching) một cách cứng nhắc, khiến ứng viên không nhận biết được các thiếu sót kỹ năng cụ thể. Ngược lại, dữ liệu thị trường tuyển dụng thường phân mảnh hoặc tĩnh, gây khó khăn cho ứng viên trong việc cập nhật các xu hướng kỹ năng theo thời gian thực.

Khóa luận này giải quyết bài toán **"phân tích độ phù hợp công việc minh bạch và có tính hành động"**. Cụ thể, đề tài tập trung vào sự lệch pha giữa hồ sơ thô của ứng viên (CV) và các yêu cầu về mặt ngữ nghĩa của các vị trí IT hiện đại, trong bối cảnh nhu cầu kỹ năng thay đổi liên tục trên thị trường.

## 1.2 Động lực nghiên cứu
Trong thực tế, khoảng cách giữa kiến thức được giảng dạy tại môi trường học thuật (ví dụ: chương trình Đại học) và yêu cầu thực tế của doanh nghiệp là một thách thức thường trực.
- **Đối với Ứng viên:** Cần một cơ chế không chỉ trả về kết quả "đạt/không đạt", mà còn giải thích *tại sao* phù hợp hoặc chưa phù hợp, và *làm thế nào* để lấp đầy khoảng trống đó thông qua các tài liệu học tập cụ thể (ví dụ: ánh xạ kỹ năng "AWS" còn thiếu tới một môn học cụ thể tại Đại học hoặc khóa học trực tuyến hiệu quả).
- **Đối với Nghiên cứu:** Hệ thống này khám phá việc ứng dụng **Các mô hình ngôn ngữ lớn (LLMs)** trong các tác vụ suy luận có cấu trúc—cụ thể là chuyển dịch từ việc tóm tắt văn bản đơn thuần sang chấm điểm đa tiêu chí (Kỹ năng cứng vs. Kỹ năng mềm vs. Chất lượng kinh nghiệm).

## 1.3 Hạn chế của các phương pháp hiện có
Các hệ thống gợi ý việc làm hiện tại thường gặp phải những hạn chế sau:
1.  **Dựa thuần vào khớp từ khóa:** Không phân biệt được giữa "số năm kinh nghiệm" và "chất lượng kinh nghiệm". Một ứng viên chỉ nhắc đến "Python" trong mô tả dự án có thể được xếp hạng tương đương với một người có 5 năm kinh nghiệm thực chiến nếu chỉ dựa vào bộ lọc từ khóa cơ bản.
2.  **Cơ chế chấm điểm "Hộp đen":** Hầu hết các hệ thống cung cấp một điểm số tương đồng (ví dụ: "85% match") mà không giải thích các yếu tố cấu thành (ví dụ: 30% từ Kỹ năng cứng, 5% từ Kỹ năng mềm).
3.  **Dữ liệu tĩnh:** Thông tin chi tiết về thị trường lao động thường dựa trên các báo cáo định kỳ thay vì các luồng dữ liệu thời gian thực, dẫn đến phân tích xu hướng kỹ năng bị lỗi thời.
4.  **Thiếu phản hồi mang tính hành động:** Các hệ thống chỉ ra các kỹ năng *còn thiếu* nhưng hiếm khi khép lại quy trình bằng cách gợi ý lộ trình học tập cụ thể, đã được kiểm chứng (ví dụ: liên kết đến các môn học nội bộ của trường đại học).

## 1.4 Mục tiêu và Câu hỏi nghiên cứu
### Mục tiêu nghiên cứu
1.  Thiết kế một **Evaluation Agent dựa trên LLM** có khả năng chấm điểm CV so với JD với sự tinh tế như con người (phân biệt độ liên quan của vai trò, độ sâu của kỹ năng và chất lượng kinh nghiệm) sử dụng một thang điểm (rubric) có cấu trúc.
2.  Cài đặt một **Cơ chế Truy vấn Lai (Hybrid Retrieval Mechanism)** kết hợp sự hiểu biết ngữ nghĩa (Vector Search) với các ràng buộc chính xác (Skill Set Overlap) để cải thiện độ liên quan của các gợi ý việc làm.
3.  Xây dựng một **Pipeline Dữ liệu Thời gian thực** (Crawler $\rightarrow$ Kafka $\rightarrow$ Spark) đảm bảo các khuyến nghị dựa trên dữ liệu thị trường mới nhất.

### Câu hỏi nghiên cứu
- **RQ1:** Làm thế nào để prompt (gợi ý) cho LLM cung cấp các chỉ số chấm điểm có cấu trúc, có thể giải thích được (Kỹ năng cứng, Kỹ năng mềm, Kinh nghiệm) thay vì các phản hồi văn bản chung chung?
- **RQ2:** Liệu chiến lược xếp hạng lai (kết hợp Vector Embeddings và khớp kỹ năng Boolean) có vượt trội hơn so với độ tương đồng vector thuần túy trong việc xác định các cơ hội việc làm phù hợp không?
- **RQ3:** Làm thế nào để tự động ánh xạ các khoảng trống kỹ năng được xác định tới các tài liệu học tập đã được kiểm chứng (ví dụ: các khóa học Đại học) để hỗ trợ việc học tập liên tục?

## 1.5 Đóng góp chính
Khóa luận này đưa ra các đóng góp sau, được ánh xạ tới các thành phần hệ thống cụ thể:

| Đóng góp | Thành phần / Cài đặt |
| :--- | :--- |
| **Rubric Đánh giá LLM có cấu trúc** | Được cài đặt trong **`EvaluationAgent`**. Khác với phản hồi dạng chat chung chung, module này tuân thủ chặt chẽ việc phân rã điểm số: Kỹ năng cứng (30đ), Kinh nghiệm làm việc (30đ), Kỹ năng mềm (5đ), v.v., trả về một đối tượng JSON có cấu trúc (`EvaluationResult`). |
| **Thuật toán Truy vấn Lai** | Được cài đặt trong **`RetrievalAgent.retrieve()`**. Đề xuất một hàm tính điểm mới: $Score = (VectorSimilarity \times 0.6) + (SkillOverlap \times 0.4)$, đảm bảo các gợi ý vừa có liên quan về mặt ngữ nghĩa vừa chính xác về mặt kỹ thuật. |
| **Lộ trình học tập lấp đầy khoảng trống** | Được cài đặt trong **`EvaluationAgent`** (Resource Enrichment). Một cơ chế tự động truy vấn `LearningResourcesService` và `UITCoursesService` để ánh xạ các kỹ năng còn thiếu tới các khóa học bên ngoài (Coursera) và nội bộ (Đại học) cụ thể. |
| **Phân tích thị trường thời gian thực** | Được cài đặt thông qua **Airflow-Kafka-Spark Pipeline**. Một kiến trúc mạnh mẽ (`crawler_dag.py`) liên tục thu thập, đẩy luồng (`producer.py`), và xử lý (`batch_consumer.py`) dữ liệu việc làm vào Kho dữ liệu Star Schema để phục vụ dashboard thời gian thực. |

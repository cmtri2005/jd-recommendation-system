# Chương 2: Tổng quan Tình hình Nghiên cứu (Related Work)

Chương này trình bày tổng quan các nghiên cứu liên quan đến bài toán Gợi ý việc làm (Job Recommendation) và Đánh giá sự phù hợp giữa Hồ sơ ứng viên (CV) và Mô tả công việc (JD). Các phương pháp tiếp cận được phân loại thành ba nhóm chính: (1) Hệ thống gợi ý truyền thống, (2) Các mô hình học sâu (Deep Learning), và (3) Các phương pháp tiếp cận hiện đại sử dụng LLM và RAG.

## 2.1 Các phương pháp Gợi ý truyền thống (Traditional Approaches)

Đây là các phương pháp tiếp cận sớm nhất, tập trung vào việc xử lý các đặc trưng rõ ràng (explicit features) từ dữ liệu văn bản.

### 2.1.1 Lọc dựa trên nội dung (Content-based Filtering)
*   **Ý tưởng cốt lõi:** Phương pháp này xây dựng hồ sơ (profile) cho ứng viên và hồ sơ cho công việc dựa trên các từ khóa (keywords). Độ tương đồng thường được tính toán bằng các độ đo thống kê như TF-IDF (Term Frequency-Inverse Document Frequency) hoặc Cosine Similarity giữa các vector từ khóa [Citation needed].
*   **Điểm mạnh:** Đơn giản, dễ cài đặt; không yêu cầu dữ liệu lịch sử của người dùng khác (không gặp vấn đề "cold start" đối với item mới).
*   **Hạn chế:**
    *   **Vấn đề đa nghĩa/đồng nghĩa:** Không xử lý được ngữ nghĩa (ví dụ: không hiểu "AI" và "Artificial Intelligence" là một, hoặc "Java" (ngôn ngữ) khác "Java" (đảo)).
    *   **Quá khớp (Over-specialization):** Chỉ gợi ý các công việc có từ khóa y hệt hồ sơ cũ, thiếu tính khám phá.

### 2.1.2 Lọc cộng tác (Collaborative Filtering - CF)
*   **Ý tưởng cốt lõi:** Dựa trên hành vi của những người dùng tương tự. Nếu ứng viên A và ứng viên B có hồ sơ giống nhau và B ứng tuyển vào công việc X, hệ thống sẽ gợi ý X cho A [Citation needed].
*   **Điểm mạnh:** Có khả năng khám phá (serendipity) – gợi ý các công việc mà ứng viên có thể không tự tìm thấy bằng từ khóa.
*   **Hạn chế:**
    *   **Cold Start:** Không hoạt động tốt với ứng viên mới hoặc công việc mới chưa có tương tác.
    *   **Sparsity:** Ma trận tương tác người dùng-công việc thường rất thưa thớt trong bài toán tuyển dụng (một người không ứng tuyển hàng nghìn việc như xem phim Netflix).

## 2.2 Các phương pháp dựa trên Học sâu (Deep Learning Approaches)

Sự ra đời của các mô hình nhúng từ (Word Embeddings) và mạng nơ-ron đã cải thiện đáng kể khả năng hiểu ngữ nghĩa.

### 2.2.1 Word Embeddings & CNN/RNN
*   **Ý tưởng cốt lõi:** Sử dụng Word2Vec, GloVe hoặc FastText để chuyển đổi văn bản thành vector liên tục (dense vectors). Các mô hình CNN (Convolutional Neural Networks) hoặc RNN/LSTM được sử dụng để trích xuất đặc trưng ngữ nghĩa từ CV và JD [Citation needed].
*   **Điểm mạnh:** Bắt được ngữ nghĩa từ vựng tốt hơn phương pháp truyền thống.
*   **Hạn chế:** Vẫn gặp khó khăn với các văn bản dài và cấu trúc phức tạp như CV. Khả năng "lý giải" (explainability) thấp – khó biết tại sao mô hình cho điểm cao/thấp.

## 2.3 Các phương pháp hiện đại dựa trên LLM và RAG (LLM & RAG Approaches)

Đây là xu hướng nghiên cứu mới nhất, tận dụng khả năng hiểu ngôn ngữ tự nhiên vượt trội của các mô hình Transformer (BERT, GPT, Llama, Claude).

*   **Ý tưởng cốt lõi:**
    *   Sử dụng **LLM** (Large Language Models) để "đọc hiểu" toàn bộ ngữ cảnh của CV và JD như một chuyên gia tuyển dụng.
    *   Sử dụng **RAG** (Retrieval-Augmented Generation) để truy vấn các công việc phù hợp từ cơ sở dữ liệu vector (Vector DB) dựa trên ngữ nghĩa thay vì từ khóa thuần túy [Citation needed].
*   **Điểm mạnh:**
    *   Hiểu sâu ngữ cảnh và sắc thái (nuance) trong mô tả kinh nghiệm.
    *   Khả năng Zero-shot reasoning: Có thể thực hiện các tác vụ suy luận phức tạp mà không cần huấn luyện lại (fine-tuning).
*   **Hạn chế:**
    *   Chi phí tính toán cao và độ trễ lớn hơn so với các phương pháp truyền thống.
    *   Vấn đề ảo giác (Hallucinations) nếu không được kiểm soát tốt bởi RAG hoặc Prompt Engineering.

## 2.4 So sánh và Khoảng trống nghiên cứu (Gap Analysis)

Bảng dưới đây so sánh các phương pháp hiện có với hệ thống được đề xuất trong khóa luận:

| Tiêu chí | Content-based/CF | Deep Learning (RNN/CNN) | LLM/Generative AI (Hiện tại) | Hệ thống đề xuất (Thesis) |
| :--- | :--- | :--- | :--- | :--- |
| **Hiểu ngữ nghĩa** | Thấp (Từ khóa) | Trung bình (Embedding tĩnh) | Cao (Contextual) | **Rất cao (Hybrid: Vector + Skill Graph)** |
| **Tính giải thích** | Thấp | Rất thấp (Hộp đen) | Trung bình (Text generation) | **Cao (Structured Scoring Rubric)** |
| **Dữ liệu thị trường**| Tĩnh (Offline) | Tĩnh (Offline) | Tĩnh (Pre-trained data) | **Thời gian thực (Real-time Pipeline)** |
| **Tính hành động** | Không (Chỉ xếp hạng) | Không | Thấp (Chỉ gợi ý chung) | **Cao (Gợi ý lộ trình học tập cụ thể)** |

### Xác định khoảng trống nghiên cứu (The Research Gap)
Mặc dù các nghiên cứu gần đây đã áp dụng LLM vào tuyển dụng, phần lớn vẫn chỉ dừng lại ở bài toán **Matching** (xếp hạng độ phù hợp). Khoảng trống nghiên cứu mà khóa luận này tập trung giải quyết bao gồm:

1.  **Thiếu tính giải thích có cấu trúc (Lack of Structured Explainability):** Hầu hết các hệ thống LLM hiện nay trả về một đoạn văn bản đánh giá tự do. Hệ thống này đề xuất một cơ chế chấm điểm định lượng đa chiều (Hard/Soft Skills, Experience) giúp chuẩn hóa kết quả đánh giá.
2.  **Thiếu vòng lặp phản hồi "Học tập" (The "Learning Gap"):** Các hệ thống hiện tại chỉ cho ứng viên biết họ "thiếu" kỹ năng gì, nhưng không chỉ ra *làm thế nào* để bổ sung. Hệ thống này tích hợp module ánh xạ lỗ hổng kỹ năng (Skill Gap) trực tiếp tới các tài nguyên học tập (Learning Resources) đã được kiểm chứng (bao gồm cả chương trình đào tạo Đại học).
3.  **Sự tĩnh tại của dữ liệu:** Nhiều hệ thống nghiên cứu sử dụng các bộ dữ liệu tĩnh (như Kaggle datasets), không phản ánh đúng nhu cầu thị trường hiện tại. Hệ thống này tích hợp pipeline Crawler-Kafka-Spark để đảm bảo tính "tươi" (freshness) của dữ liệu khuyến nghị.

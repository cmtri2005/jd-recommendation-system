# Matching Evaluation System

Hệ thống đánh giá độ chính xác và tin cậy của matching system bằng cách so sánh kết quả với ground truth dataset.

## Tổng quan

Hệ thống evaluation này thực hiện:
1. **Input**: 1 JD - 1 Resume pair → Output: Matching score (0-1)
2. **Ground Truth**: Tập mẫu với JD-Resume pairs đã được label (pass/fail dựa trên threshold >= 0.7)
3. **Evaluation**: So sánh kết quả matching với ground truth để đánh giá độ chính xác

## Cấu trúc

- `matching_evaluator.py`: Class chính để đánh giá matching system
- `test_matching_evaluation.py`: Script để chạy evaluation

## Cách sử dụng

### 1. Tạo Ground Truth Dataset

Ground truth dataset có thể là file JSON hoặc CSV với format:

**JSON format:**
```json
[
  {
    "jd_path": "resume_jd/job1.docx",
    "resume_path": "resume_jd/resume1.pdf",
    "label": "pass"
  },
  {
    "jd_path": "resume_jd/job2.docx",
    "resume_path": "resume_jd/resume2.pdf",
    "score": 0.85
  }
]
```

**CSV format:**
```csv
jd_path,resume_path,label
resume_jd/job1.docx,resume_jd/resume1.pdf,pass
resume_jd/job2.docx,resume_jd/resume2.pdf,fail
```

**Lưu ý:**
- `label`: "pass" hoặc "fail" (dựa trên threshold >= 0.7)
- `score`: Score từ 0.0 đến 1.0 (sẽ tự động convert sang label)

### 2. Tạo sample ground truth template

```bash
python test_matching_evaluation.py --create-sample --ground-truth data/ground_truth.json
```

### 3. Chạy Evaluation

```bash
python test_matching_evaluation.py \
    --ground-truth data/ground_truth.json \
    --threshold 0.7 \
    --output results/evaluation_results.json
```

**Parameters:**
- `--ground-truth`: Đường dẫn đến file ground truth
- `--threshold`: Ngưỡng để phân loại pass/fail (mặc định: 0.7)
- `--output`: Đường dẫn để lưu kết quả evaluation (optional)

### 4. Xem kết quả

Script sẽ in ra:
- **Classification Metrics**: Accuracy, Precision, Recall, F1-score
- **Score Metrics**: Correlation, MAE, MSE, RMSE
- **Confusion Matrix**: Ma trận nhầm lẫn
- **Detailed Report**: Chi tiết cho từng class

## Metrics được tính

### Classification Metrics
- **Accuracy**: Tỷ lệ dự đoán đúng tổng thể
- **Precision**: Tỷ lệ dự đoán "pass" là đúng
- **Recall**: Tỷ lệ tìm được các "pass" thực sự
- **F1-score**: Harmonic mean của Precision và Recall

### Score Metrics
- **Correlation**: Tương quan giữa predicted scores và ground truth scores
- **MAE**: Mean Absolute Error
- **MSE**: Mean Squared Error
- **RMSE**: Root Mean Squared Error

## Ví dụ Output

```
================================================================================
MATCHING SYSTEM EVALUATION REPORT
================================================================================

Threshold: 0.7
Number of samples: 50

--------------------------------------------------------------------------------
CLASSIFICATION METRICS
--------------------------------------------------------------------------------
Accuracy:  0.8600 (86.00%)
Precision: 0.8750 (87.50%)
Recall:    0.8235 (82.35%)
F1 Score:  0.8485 (84.85%)

--------------------------------------------------------------------------------
SCORE METRICS
--------------------------------------------------------------------------------
Score Correlation: 0.9234
MAE (Mean Absolute Error): 0.1234
MSE (Mean Squared Error):  0.0234
RMSE (Root Mean Squared Error): 0.1529

--------------------------------------------------------------------------------
CONFUSION MATRIX
--------------------------------------------------------------------------------

            Predicted Fail  Predicted Pass
Actual Fail 15              3
Actual Pass 2               30
```

## Code Example

```python
from core.evaluation.matching_evaluator import MatchingEvaluator
from core.agents.orchestrator import Orchestrator

# Initialize evaluator
evaluator = MatchingEvaluator(threshold=0.7)

# Load ground truth
ground_truth = evaluator.load_ground_truth("data/ground_truth.json")

# Run matching and get predictions
predictions = [
    {"jd_path": "jd1.docx", "resume_path": "resume1.pdf", "score": 0.85},
    {"jd_path": "jd2.docx", "resume_path": "resume2.pdf", "score": 0.65},
]

# Evaluate
results = evaluator.evaluate(ground_truth, predictions)

# Print report
evaluator.print_evaluation_report(results)
```

## Lưu ý

1. **File paths**: Có thể dùng relative hoặc absolute paths. Relative paths sẽ được resolve từ thư mục script.
2. **Threshold**: Mặc định là 0.7 (score >= 0.7 = pass). Có thể thay đổi khi khởi tạo evaluator.
3. **Score normalization**: Evaluation agent trả về score từ 0-100, được normalize về 0-1 để so sánh với threshold.

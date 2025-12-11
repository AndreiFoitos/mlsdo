---
language:
- en
license_link: LICENSE
library_name: transformers
tags:
- sentiment-analysis
- classification
- bert
datasets:
- Amazon book reviews
metrics:
- accuracy
- binary_cross_entropy
base_model: google/bert_uncased_L-2_H-128_A-2

model-index:
- name: Book Review Sentiment Classification Model
  results:
  - task:
      type: text-classification
      name: Sentiment Analysis (Positive vs. Not Positive)
    dataset:
      type: custom_book_reviews
      name: Book Reviews Dataset (internal)
      split: test
    metrics:
      - type: accuracy
        value: 0.42
        name: Test Accuracy
      - type: binary_cross_entropy
        value: 58
        name: Test Loss
---

# Model Card for Book Review Sentiment Classification Model

The Book Review Sentiment Classification Model predicts whether a given book review is positive (rating > 3) or not, based on its title and text. The model is a fine-tuned version of `google/bert_uncased_L-2_H-128_A-2` on a custom dataset of book reviews sourced from a PostgreSQL database.

## Model Details

### Model Description

- **Developed by:** Daniel Feitosa and Jesse Maarleveld
- **Model type:** Binary Sentiment Classifier using BERT
- **Language(s):** English
- **License:** Refer to [LICENSE](LICENSE) file.
- **Finetuned from model:** [google/bert_uncased_L-2_H-128_A-2](https://huggingface.co/google/bert_uncased_L-2_H-128_A-2)

This model leverages a lightweight BERT architecture to classify book reviews as positive or not. It takes as input the concatenation of the review title and text, and outputs a binary prediction.

### Model Sources

- **Repository:** Private/internal (not publicly available)
- **Paper/Documentation:** N/A

## Uses

### Direct Use

This model is intended for sentiment analysis on English-language book reviews. Given a title and text of a review, it provides a prediction of whether the review sentiment is positive (>3 rating) or not.

### Downstream Use

The model can be integrated into recommendation systems, review summarization pipelines, or used as a signal for content moderation or quality assessment in online bookstores, review aggregators, or recommendation engines.

### Out-of-Scope Use

- **Misuse:** This model is not intended for classification tasks outside English-language book reviews.
- **Limitations:** 
  - The model might not perform well on very short or extremely long texts (beyond the truncation limit).
  - It may not generalize well to other domains (e.g., movie reviews, product reviews) without further fine-tuning.

## Bias, Risks, and Limitations

The model's performance and potential biases are directly related to the data it was trained on. If the underlying dataset does not represent a diverse set of authors, genres, or reading communities, the model might show bias in its predictions (e.g., favoring certain writing styles or popular genres).

### Recommendations

- **Data Updates:** Periodically retrain the model on newer and more diverse data to reduce bias and improve robustness.
- **Human-in-the-Loop:** Complement the model's predictions with human review when making critical decisions.
- **Transparency:** Provide clear explanations to users on how the model makes predictions and acknowledge potential biases.

## How to Get Started with the Model

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load the fine-tuned model
model_name = "path/to/your/fine-tuned-model"  # or MLflow model URI
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

review_title = "Amazing Story!"
review_text = "I absolutely loved the character development and the plot twists."
input_text = f"{review_title}. {review_text}"

inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
with torch.no_grad():
    outputs = model(**inputs)
    probabilities = torch.sigmoid(outputs.logits)
    prediction = (probabilities > 0.5).int()
    sentiment = "Positive" if prediction.item() == 1 else "Not Positive"

print(f"Sentiment: {sentiment}")
```

## Training Details

### Training Data

- **Data Source:** Book reviews loaded from a PostgreSQL database.
- **Labeling:** Binary label derived from the review's rating (positive if rating > 3, otherwise not).

### Training Procedure

1. **Preprocessing:**
   - Text concatenation of `title` and `text`.
   - Tokenization using BERT tokenizer with max_length=512.
   - Conversion of rating into a binary label.

2. **Data Splitting:**
   - Data was split into training, validation, and test sets (approx. 80/10/10).

3. **Training Configuration:**
   - **Base Model:** `google/bert_uncased_L-2_H-128_A-2`
   - **Number of Epochs:** 1
   - **Learning Rate:** 3e-5
   - **Batch Size:** 16

4. **Evaluation Metrics:**
   - Accuracy
   - Binary Cross-Entropy Loss

### Speeds, Sizes, Times

- **Training Time:** Dependent on hardware and dataset size; for ~500 samples, training is typically a few minutes on a CPU.
- **Model Size:** Approximately the size of the BERT base model plus classifier head.

## Evaluation

### Testing Data and Metrics

- **Test Split:** ~10% of the dataset held out for testing.
- **Metrics:** 
  - **Accuracy:** Measures how often the model classifies correctly.
  - **Binary Cross-Entropy Loss:** Measures the error between predicted probabilities and actual labels.

### Results

- **Test Accuracy:** 0.42
- **Test Loss (BCE):** 58

#### Summary

The model shows promising accuracy for classifying the sentiment of book reviews. Further tuning, additional data, and longer training might improve results.

## Environmental Impact

Training was done on CPU with minimal computational overhead. Actual environmental impact is small given the relatively small dataset and short training duration.

## Technical Specifications

### Model Architecture and Objective

- **Architecture:** A BERT-based classification head for binary sentiment analysis.
- **Objective:** Minimizing binary cross-entropy between predictions and ground truth labels.

### Compute Infrastructure

- **Hardware:** CPU environment (no GPU assumed).
- **Software:** Python 3.9, PyTorch, Hugging Face Transformers, Datasets, TorchMetrics, MLflow, psycopg2 for database access.

## Glossary

- **Binary Cross-Entropy Loss:** A loss function used for binary classification tasks.
- **BERT:** Bidirectional Encoder Representations from Transformers, a transformer-based NLP model.
- **Sentiment Analysis:** Determining if text expresses positive, neutral, or negative sentiment.

## Model Card Authors

- Daniel Feitosa

## Model Card Contact

- **Email:** [d.feitosa@rug.nl](mailto:d.feitosa@rug.nl)

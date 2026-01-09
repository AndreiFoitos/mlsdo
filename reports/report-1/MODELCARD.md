---
base_model: distilbert-base-uncased
datasets:
  - JiraRepos (Apache)
  - MiningDesignDecisions (MDD)
language:
  - en
library_name: transformers
license_link: LICENSE
metrics:
  - accuracy
  - f1
  - precision
  - recall
model-index:
  - name: Architectural Design Decision (ADD) Classifier
    results:
      - dataset:
          name: MiningDesignDecisions (internal)
          split: test
          type: issue-tracking-data
        metrics:
          - name: Test Accuracy
            type: accuracy
            value: 0.79
          - name: Test F1 Score
            type: f1
            value: 0.76
          - name: Test Precision
            type: precision
            value: 0.72
          - name: Test Recall
            type: recall
            value: 0.8
        task:
          name: Binary Classification (ADD vs. Non-ADD)
          type: text-classification
tags:
  - architecture-mining
  - software-engineering
  - distilbert
  - classification
---

# Model Card for Architectural Design Decision (ADD) Classifier

The Architectural Design Decision (ADD) Classifier is a machine learning model designed to automatically identify whether a software issue (ticket) contains an Architectural Design Decision. It predicts a binary label (`0` for Non-ADD, `1` for ADD) based on the textual content of the issue's summary and description. The model we are currently using is a fine-tuned version of `distilbert-base-uncased`, which we chose as an upgrade from the initial model that we used `google/bert_uncased_L-2_H-128_A-2`, which had inferior results due to its more simple architecure.

## Model Details

### Model Description

- **Developed by:** Group 6 (Andrei Foitoș, Andrei-George Iclodean, and Yuwen Zhou)
- **Model type:** Binary Text Classifier using DistilBERT
- **Language(s):** English
- __Finetuned from models:__ [distilbert-base-uncased](https://huggingface.co/distilbert-base-uncased) (and initially [google/bert_uncased_L-2_H-128_A-2](https://huggingface.co/google/bert_uncased_L-2_H-128_A-2))

This model leverages the DistilBERT architecture, a distilled version of BERT that is smaller and faster while retaining most of the performance. It takes as input the concatenated text of a Jira issue's summary and description and outputs the probability of it being an architectural decision.

### Model Sources

- __Repository:__ [Group 6 Project](https://gitlab.com/rug-cs/courses/mlops/2025-2026/students/group-6/group-6-project/-/tree/develop?ref_type=heads)
- **Data Source:** [MiningDesignDecisions](https://github.com/mining-design-decisions) and [JiraRepos](https://github.com/mining-design-decisions) datasets.

### Training Procedure

- **Optimizer:** AdamW with a Learning Rate of 2e-5
- **Epochs:** 4
- **Batch Size:** 8
- **Validation Usage:** The validation set was used for early stopping; training halted if the Validation F1-score did not improve for two consecutive epochs to prevent overfitting. The test set was held out entirely for the final unbiased evaluation.

## Initial results

- **Test Accuracy:** 0.79
- **Test F1 Score:** 0.76
- **Test Precision:** 0.72
- **Test Recall:** 0.80

### Interpretation
The model is optimized for Recall (0.80) to ensure that software architects miss very few actual decisions. The lower Precision (0.72) is an intentional trade-off. The system acts as a broad discovery tool where human experts perform a final quick filter of false positives.

## Uses

### Direct Use

This model is intended for **software engineering researchers** and **practitioners** who need to mine architectural knowledge from large-scale issue tracking systems (like Jira). Given an issue's summary and description, it filters irrelevant bugs and features to highlight potential architectural decisions.

### Downstream Use

The model can be integrated into:

- **Technical Debt Analysis:** Identifying historical architectural changes.
- **Knowledge Management Systems:** Automatically tagging issues that impact the system architecture.
- **Change Impact Analysis:** filtering for high-impact architectural issues.

### Out-of-Scope Use

- **Non-English Data:** The model is trained exclusively on English-language open-source projects.
- **Chat/Email Analysis:** The model is specialized for the structured "Summary + Description" format of issue trackers and may not perform well on conversational text.
- **General Sentiment Analysis:** This is not a sentiment classifier; it detects technical architectural content.

## Bias, Risks, and Limitations

### Limitations

- **Precision vs. Recall:** The model achieves a Recall of **0.80**, meaning it successfully captures most architectural decisions. However, with a Precision of **0.72**, it produces a noticeable number of false positives (approx. 28%). Human verification is recommended for high-precision tasks.
- **Domain Specificity:** Trained primarily on Apache projects (infrastructure/server software). It may not generalize perfectly to mobile apps, games, or UI-heavy projects with different terminologies.

### Ethical Considerations

The training data is derived from specific open-source communities. This may introduce bias toward the development culture and documentation styles of those specific projects (e.g., Apache Foundation). Decisions documented in non-standard ways or by non-native English speakers may be under-represented.

## Improvement Strategies
1. **Domain-Specific Pre-training:** Utilizing a model like SEBERT, pre-trained on software engineering corpora, to handle technical jargon more effectively. 
2. **Data Augmentation:** Using 'Back-Translation' (English to German and back) on the minority ADD samples to balance the dataset. 
3. **Active Learning:** Implementing a UI feedback loop where users flag false positives to retrain the model.
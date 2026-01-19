import os
import time
import datasets
import psycopg2
import typing
import torch
import torch.nn as nn
import torchmetrics
import transformers
import mlflow
import numpy as np
from sklearn.utils.class_weight import compute_class_weight

POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://postgres:pw1@localhost:5432/reviews_db')
MLFLOW_TRACKING_URL = os.getenv('MLFLOW_TRACKING_URL', 'http://localhost:5000')
MLFLOW_MODEL_NAME = os.getenv('MLFLOW_MODEL_NAME', 'add_detection_model')

MODEL_NAME = "distilbert-base-uncased"
LEARNING_RATE = 2e-5
BATCH_SIZE = 4
EPOCHS = 4
MAX_LENGTH = 256
LIMIT = ""

# CI quick mode
CI_MODE = os.getenv("CI_MODE", "false").strip().lower() in ("1", "true", "yes", "y")
CI_TRAIN_MAX = int(os.getenv("CI_TRAIN_MAX", "300"))   # keep small for < 1h
CI_VAL_MAX = int(os.getenv("CI_VAL_MAX", "120"))
CI_TEST_MAX = int(os.getenv("CI_TEST_MAX", "120"))

accuracy_metric = torchmetrics.Accuracy(task='binary')
f1_metric = torchmetrics.F1Score(task='binary')
precision_metric = torchmetrics.Precision(task='binary')
recall_metric = torchmetrics.Recall(task='binary')

class WeightedTrainer(transformers.Trainer):
    def __init__(self, class_weights, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss_fct = nn.CrossEntropyLoss(weight=self.class_weights)
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

class Issue:
    __slots__ = ('key', 'summary', 'description', 'is_add')

    def __init__(self, key: str, summary: str, description: str, is_add: int):
        self.key = key
        self.summary = summary or ""
        self.description = description or ""
        self.is_add = is_add

def load_data_from_db(connection_string: typing.Optional[str] = None) -> typing.List[Issue]:
    return list(_load_data_from_db_helper(connection_string))

def _load_data_from_db_helper(connection_string: typing.Optional[str] = None) -> typing.Iterator[Issue]:
    if connection_string is None:
        connection_string = os.environ.get('POSTGRES_URL')

    query = f"""
        SELECT
            issue_key,
            summary,
            description,
            (CASE WHEN label_existence = TRUE OR label_executive = TRUE OR label_property = TRUE THEN 1 ELSE 0 END) as is_add
        FROM processed_issues
        {LIMIT};
    """

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                yield Issue(row[0], row[1], row[2], row[3])

def load_model(model_name: str):
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
    model = transformers.AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        problem_type='single_label_classification'
    )
    return tokenizer, model

def tokenize_issues(issues: list[Issue], tokenizer):
    valid_issues = [i for i in issues if len((i.summary + i.description).split()) > 10]

    tokenized = [
        tokenizer(
            f"{issue.summary}. {issue.description}",
            padding='max_length',
            max_length=MAX_LENGTH,
            truncation=True,
            add_special_tokens=True
        )
        for issue in valid_issues
    ]

    combined = [
        {'label': int(issue.is_add)} | text
        for text, issue in zip(tokenized, valid_issues)
    ]
    return datasets.Dataset.from_list(combined)

def compute_metrics(eval_pred: transformers.EvalPrediction):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)

    preds_tensor = torch.from_numpy(predictions)
    truth_tensor = torch.from_numpy(labels)

    return {
        'accuracy': accuracy_metric(preds_tensor, truth_tensor).item(),
        'f1_score': f1_metric(preds_tensor, truth_tensor).item(),
        'precision': precision_metric(preds_tensor, truth_tensor).item(),
        'recall': recall_metric(preds_tensor, truth_tensor).item()
    }


def train_model(model, training_data, validation_data, class_weights):
    # CI mode: reduce epochs + avoid checkpoint saving (fast)
    epochs = 1 if CI_MODE else EPOCHS
    warmup = 0 if CI_MODE else 100
    save_strategy = "no" if CI_MODE else "epoch"

    training_args = transformers.TrainingArguments(
        output_dir='./training_logs',
        num_train_epochs=epochs,
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        warmup_steps=warmup,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy=save_strategy,
        load_best_model_at_end=(not CI_MODE),  # CI doesn't need best-model selection
        metric_for_best_model="f1_score",
        report_to="none"
    )

    trainer = WeightedTrainer(
        class_weights=class_weights,
        model=model,
        args=training_args,
        train_dataset=training_data,
        eval_dataset=validation_data,
        compute_metrics=compute_metrics
    )
    trainer.train()
    return trainer


def split_dataset(dataset, test_size=0.15, val_size=0.15):
    mapping = dataset.train_test_split(test_size=(test_size + val_size))
    train = mapping['train']

    remainder = mapping['test']
    val_rel_size = val_size / (test_size + val_size)
    mapping_val = remainder.train_test_split(test_size=(1 - val_rel_size))

    val, test = mapping_val['train'], mapping_val['test']
    return train, val, test


def _cap_dataset(ds: datasets.Dataset, cap: int) -> datasets.Dataset:
    if cap <= 0:
        return ds
    n = min(len(ds), cap)
    if n == len(ds):
        return ds
    return ds.select(range(n))


def _get_tracking_uri() -> str:
    # compatible with both env var names
    return (os.getenv("MLFLOW_TRACKING_URI")
            or os.getenv("MLFLOW_TRACKING_URL")
            or MLFLOW_TRACKING_URL)


def main():
    mlflow.set_tracking_uri(_get_tracking_uri())

    with mlflow.start_run(run_name=f"training_{int(time.time())}"):
        mlflow.autolog(log_models=False)
        mlflow.log_params({
            "learning_rate": LEARNING_RATE,
            "batch_size": BATCH_SIZE,
            "epochs": (1 if CI_MODE else EPOCHS),
            "max_length": MAX_LENGTH,
            "ci_mode": CI_MODE,
            "ci_train_max": CI_TRAIN_MAX,
            "ci_val_max": CI_VAL_MAX,
            "ci_test_max": CI_TEST_MAX,
        })

        print('1. Loading Data...')
        issues = load_data_from_db()
        if not issues:
            print("No data found. Ensure DB is populated.")
            return

        print('2. Initializing Model...')
        tokenizer, model = load_model(MODEL_NAME)

        print('3. Tokenizing and Filtering Data...')
        dataset = tokenize_issues(issues, tokenizer)

        print('4. Splitting Data (70/15/15)...')
        train, val, test = split_dataset(dataset)

        if CI_MODE:
            train = _cap_dataset(train, CI_TRAIN_MAX)
            val = _cap_dataset(val, CI_VAL_MAX)
            test = _cap_dataset(test, CI_TEST_MAX)
            print(f"[CI_MODE] Capped sizes: train={len(train)} val={len(val)} test={len(test)}")

        train_labels = [x['label'] for x in train]
        weights = compute_class_weight(
            class_weight='balanced',
            classes=np.unique(train_labels),
            y=train_labels
        )

        device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        class_weights = torch.tensor(weights, dtype=torch.float).to(device)
        model.to(device)
        print(f"Calculated Class Weights: {weights}")

        print('5. Training...')
        trainer = train_model(model, train, val, class_weights)

        print('6. Evaluating on Test Set (Unbiased)...')
        results = trainer.evaluate(test)
        print(results)

        mlflow.log_metrics({
            "test_accuracy": results.get("eval_accuracy"),
            "test_f1": results.get("eval_f1_score"),
            "test_precision": results.get("eval_precision"),
            "test_recall": results.get("eval_recall"),
        })

        print('7. Storing Model Artifacts...')
        if CI_MODE:
            print("[CI_MODE] Skipping mlflow model artifact logging to avoid MinIO/S3 credentials requirement.")
        else:
            mlflow.pytorch.log_model(
                model,
                artifact_path='trained-model',
                registered_model_name=os.getenv('MLFLOW_MODEL_NAME')
            )

            mlflow.transformers.log_model(
                transformers.pipeline('text-classification', model=model, tokenizer=tokenizer),
                artifact_path="pipeline"
            )

        print('Done.')

if __name__ == '__main__':
    main()

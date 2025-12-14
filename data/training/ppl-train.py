import os
import typing
import datasets
import psycopg2
import torch
import torchmetrics
import transformers
import mlflow
import numpy as np

required_env = ["POSTGRES_URL", "MLFLOW_TRACKING_URL", "MLFLOW_MODEL_NAME"]
for env in required_env:
    if os.environ.get(env) is None:
        raise ValueError(f'{env} environment variable not set')

MODEL_NAME = "distilbert-base-uncased"
LEARNING_RATE = 2e-5
BATCH_SIZE = 8
EPOCHS = 4
LIMIT = "" 

accuracy_metric = torchmetrics.Accuracy(task='binary')
f1_metric = torchmetrics.F1Score(task='binary')
precision_metric = torchmetrics.Precision(task='binary')
recall_metric = torchmetrics.Recall(task='binary')

class Issue:
    __slots__ = ('key', 'summary', 'description', 'is_add')

    def __init__(self, key: str, summary: str, description: str, is_add: int):
        self.key = key
        self.summary = summary or ""
        self.description = description or ""
        self.is_add = is_add

def load_data_from_db(connection_string: str | None = None) -> list[Issue]:
    return list(_load_data_from_db_helper(connection_string))

def _load_data_from_db_helper(connection_string: str | None = None) -> typing.Iterator[Issue]:
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
    tokenized = [
        tokenizer(
            f"{issue.summary}. {issue.description}",
            padding='max_length',
            max_length=512,
            truncation=True,
            add_special_tokens=True
        )
        for issue in issues
    ]
    
    combined = [
        {'label': int(issue.is_add)} | text
        for text, issue in zip(tokenized, issues)
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

def train_model(model, training_data, validation_data):
    training_args = transformers.TrainingArguments(
        output_dir='./training_logs',
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_score",
        use_cpu=False 
    )

    trainer = transformers.Trainer(
        model=model,
        args=training_args,
        train_dataset=training_data,
        eval_dataset=validation_data,
        compute_metrics=compute_metrics
    )
    trainer.train()
    return trainer

def split_dataset(dataset, test_size=0.15, val_size=0.15):
    train_size = 1 - test_size - val_size
    mapping = dataset.train_test_split(test_size=(test_size + val_size))
    train = mapping['train']
    
    remainder = mapping['test']
    val_rel_size = val_size / (test_size + val_size)
    mapping_val = remainder.train_test_split(test_size=(1-val_rel_size))
    
    val, test = mapping_val['train'], mapping_val['test']
    return train, val, test

def main():
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URL'))
    
    with mlflow.start_run():
        mlflow.autolog()
        
        print('1. Loading Data...')
        issues = load_data_from_db()
        if not issues:
            print("No data found. Ensure DB is populated.")
            return

        print('2. Initializing Model...')
        tokenizer, model = load_model(MODEL_NAME)
        
        print('3. Tokenizing Data...')
        dataset = tokenize_issues(issues, tokenizer)
        
        print('4. Splitting Data...')
        train, val, test = split_dataset(dataset)
        
        print('5. Training...')
        trainer = train_model(model, train, val)
        
        print('6. Evaluating on Test Set...')
        results = trainer.evaluate(test)
        print(results)

        mlflow.log_metrics({
            "test_accuracy": results.get("eval_accuracy"),
            "test_f1": results.get("eval_f1_score"),
            "test_precision": results.get("eval_precision"),
            "test_recall": results.get("eval_recall"),
        })

        print('7. Storing Model Artifacts...')
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
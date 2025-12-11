import os
import typing

import datasets
import psycopg2
import torch
import torchmetrics
import transformers
import mlflow


for env in ["POSTGRES_URL", "MLFLOW_TRACKING_URL", "MLFLOW_MODEL_NAME"]:
    if os.environ.get(env) is None:
        raise ValueError(f'{env} environment variable not set')


MODEL_NAME = "google/bert_uncased_L-2_H-128_A-2"
LEARNING_RATE = 3e-5
BATCH_SIZE = 16
EPOCHS = 1
LIMIT = "LIMIT 500" # Set to "" to use all data
accuracy_metric = torchmetrics.Accuracy(task='binary', threshold=0.5)

class Review:
    __slots__ = ('title', 'text', 'rating')

    def __init__(self, title: str, text: str, rating: int):
        self.title = title
        self.text = text
        self.rating = rating


def load_data_from_db(connection_string: str | None = None) -> list[Review]:
    return list(_load_data_from_db_helper(connection_string))


def _load_data_from_db_helper(connection_string: str | None = None) -> typing.Iterator[Review]:
    if connection_string is None:
        connection_string = os.environ.get('POSTGRES_URL')
    if connection_string is None:
        raise ValueError('No connection string provided.')

    with psycopg2.connect(connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT review_title, review_text, rating FROM book_reviews {LIMIT};')
            for title, text, rating in cursor.fetchall():
                yield Review(title, text, rating)


def load_model(model_name: str):
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
    model = transformers.AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=1,
        problem_type='multi_label_classification',
    )
    return tokenizer, model


def tokenize_reviews(reviews: list[Review], tokenizer):
    tokenized = [
        tokenizer(
            f'{review.title}. {review.text}',
            padding='max_length',
            max_length=512,
            truncation=True,
            add_special_tokens=True
        )
        for review in reviews
    ]
    # BERT expects its inputs to be dictionaries
    combined = [
        {'label': [review.rating > 3]} | text
        for text, review in zip(tokenized, reviews)
    ]
    return datasets.Dataset.from_list(combined)


def predict(model, dataset):
    device = torch.device("cpu") # force CPU (in case GPU is default)
    model = model.to(device)
    with torch.no_grad():
        inputs_ids = torch.tensor(dataset['input_ids']).to(device)
        attention_masks = torch.tensor(dataset['attention_mask']).to(device)
        token_type_ids = torch.tensor(dataset['token_type_ids']).to(device)
        out = model(input_ids=inputs_ids,
                    attention_mask=attention_masks,
                    token_type_ids=token_type_ids)
        probabilities = torch.nn.functional.sigmoid(out.logits)
        predictions = probabilities.round()
        return predictions


def get_labels_from_dataset(dataset):
    return torch.tensor(dataset['label'], dtype=torch.float)


def evaluate_model(predictions, ground_truths):
    loss = torch.nn.functional.binary_cross_entropy(predictions, ground_truths).item()
    accuracy = accuracy_metric(predictions, ground_truths).item()
    return {'loss': loss, 'accuracy': accuracy}


def split_dataset(dataset, *, test_size=0.1, val_size=0.1):
    train_size= 1 - test_size - val_size
    mapping = dataset.train_test_split(train_size=train_size)
    train, remainder = mapping['train'], mapping['test']
    frac = val_size / (test_size + val_size)
    mapping = remainder.train_test_split(frac)
    val, test = mapping['train'], mapping['test']
    return train, val, test


def get_training_params():
    args = transformers.TrainingArguments(
        output_dir='./training_logs',
        save_strategy='epoch',
        load_best_model_at_end=True,
        eval_strategy='epoch',
    )
    args = args.set_training(
        learning_rate=LEARNING_RATE,
        batch_size=BATCH_SIZE,
        num_epochs=EPOCHS
    )
    return args


def compute_metrics(eval_pred: transformers.EvalPrediction):
    with torch.no_grad():
        truth = torch.from_numpy(eval_pred.label_ids)
        predictions = torch.from_numpy(eval_pred.predictions)
        predictions = torch.nn.functional.sigmoid(predictions)
        return evaluate_model(predictions, truth)


def train_model(model, training_data, validation_data, training_args):
    trainer = transformers.Trainer(
        model=model,
        args=training_args,
        train_dataset=training_data,
        eval_dataset=validation_data,
        compute_metrics=compute_metrics,
    )
    trainer.train()


def main():
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URL'))
    with mlflow.start_run():
        mlflow.autolog()
        print('Loading model')
        tokenizer, model = load_model(MODEL_NAME)
        print('Loading data')
        reviews = list(load_data_from_db())
        print('Tokenizing')
        data = tokenize_reviews(reviews, tokenizer)
        print('Splitting')
        train, val, test = split_dataset(data)
        print('Training')
        training_args = get_training_params()
        train_model(model, train, val, training_args)
        print('Predicting')
        predictions = predict(model, test)
        print('Evaluating')
        truth = get_labels_from_dataset(test)
        result = evaluate_model(predictions, truth)
        print(result)
        for key, value in result.items():
            mlflow.log_metric(f'test_{key}', value)
        print('Storing Model')
        mlflow.pytorch.log_model(
            model,
            artifact_path='trained-model',
            registered_model_name=os.getenv('MLFLOW_MODEL_NAME')
        )
        print('Done')


if __name__ == '__main__':
    main()

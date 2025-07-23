import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict
import os
from collections import Counter
from transformers import AutoTokenizer
from datasets import concatenate_datasets

def load_hdfs_dataset(log_path="../data/HDFS_100k.log_structured.csv", label_path="../data/anomaly_label.csv"):
    import re

    df_logs = pd.read_csv(log_path)
    df_labels = pd.read_csv(label_path)

    # Extract block ID from Content
    df_logs['BlockId'] = df_logs['Content'].str.extract(r'(blk_[\-]?\d+)')

    # Drop rows without BlockId (safety)
    df_logs = df_logs.dropna(subset=['BlockId'])

    # Merge labels
    df = pd.merge(df_logs, df_labels, on='BlockId')

    # Map 'Anomaly' to 1, 'Normal' to 0
    df['label'] = df['Label'].map({'Anomaly': 1, 'Normal': 0})

    from collections import Counter
    print("Label distribution:", Counter(df['label']))

    return df[['Content', 'label']]



def prepare_dataset():
    df = load_hdfs_dataset()
    print("Label distribution:", Counter(df['label']))

    # Convert to HuggingFace Dataset
    dataset = Dataset.from_pandas(df)

    # Cast label to ClassLabel so stratified splitting works
    from datasets import ClassLabel
    label_values = sorted(df['label'].unique())  # [0, 1]
    class_label = ClassLabel(num_classes=2, names=[str(v) for v in label_values])
    dataset = dataset.cast_column("label", class_label)

    # Train-test split with stratification
    dataset = dataset.train_test_split(test_size=0.2, stratify_by_column="label")

    train = dataset["train"]
    test = dataset["test"]

    print("Train label distribution:", Counter(train["label"]))
    print("Test label distribution:", Counter(test["label"]))

    # Oversample minority class in train set
    train_df = train.to_pandas()
    minority = train_df[train_df['label'] == 1]
    majority = train_df[train_df['label'] == 0]
    oversample_factor = max(1, int(len(majority) / max(1, len(minority))))
    minority_oversampled = pd.concat([minority] * oversample_factor, ignore_index=True)
    train_df_oversampled = pd.concat([majority, minority_oversampled], ignore_index=True)
    train = Dataset.from_pandas(train_df_oversampled)
    train = train.cast_column("label", class_label)

    tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-mini", local_files_only=True)
    MAX_LENGTH = 128

    def tokenize(example):
        return tokenizer(
            example["Content"],
            padding="max_length",
            truncation=True,
            max_length=MAX_LENGTH
        )

    train = train.map(tokenize, batched=True)
    test = test.map(tokenize, batched=True)

    return DatasetDict({"train": train, "test": test})


if __name__ == "__main__":
    tokenized = prepare_dataset()
    print(tokenized)
    from collections import Counter

    train_labels = tokenized["train"]["label"]
    test_labels = tokenized["test"]["label"]

    print("Train label distribution:", Counter(train_labels))
    print("Test label distribution:", Counter(test_labels))


from prepare_data import prepare_dataset
from transformers import AutoModelForSequenceClassification
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, ConfusionMatrixDisplay
)
import torch
from collections import Counter
import json
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

def evaluate_model(model_dir="bert-mini-hdfs", threshold=0.6, class_weight=1.5):
    model = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)
    dataset = prepare_dataset()  # loads tokenized train/test splits with labels

    train_dataset = dataset["train"]
    test_dataset = dataset["test"]
    test_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    true_labels = test_dataset["label"]
    pred_labels = []

    model.eval()
    with torch.no_grad():
        for batch in torch.utils.data.DataLoader(test_dataset, batch_size=32):
            outputs = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"])
            probs = torch.softmax(outputs.logits, dim=1)
            preds = (probs[:, 1] > threshold).long()
            pred_labels.extend(preds.cpu().numpy())

    acc = accuracy_score(true_labels, pred_labels)
    prec = precision_score(true_labels, pred_labels)
    rec = recall_score(true_labels, pred_labels)
    f1 = f1_score(true_labels, pred_labels)
    tn, fp, fn, tp = confusion_matrix(true_labels, pred_labels).ravel()

    # Plot and save confusion matrix
    cm = confusion_matrix(true_labels, pred_labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["BENIGN", "ATTACK"])
    disp.plot(cmap=plt.cm.Blues)
    plt.title(f"Confusion Matrix: {model_dir}")
    plt.savefig(f"{model_dir}_confusion_matrix.png")
    plt.close()

    results = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn)
    }

    log_experiment(
        results=results,
        model_name=model_dir,
        dataset_name="HDFS Log Anomaly Dataset",
        class_weight=class_weight,
        threshold=threshold,
    label_distribution={
        "train": {str(i): int(count) for i, count in enumerate(torch.tensor(train_dataset["label"]).bincount())},
        "test": {str(i): int(count) for i, count in enumerate(torch.tensor(test_dataset["label"]).bincount())}
        }
    ) 

    return results

def log_experiment(results, model_name, dataset_name, class_weight=None, threshold=0.5, label_distribution=None):
    log_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": model_name,
        "dataset": dataset_name,
        "class_weight_multiplier": class_weight,
        "threshold": threshold,
        "accuracy": results["accuracy"],
        "precision": results["precision"],
        "recall": results["recall"],
        "f1": results["f1"],
        "true_positive": results["true_positive"],
        "false_positive": results["false_positive"],
        "true_negative": results["true_negative"],
        "false_negative": results["false_negative"],
        "label_distribution": label_distribution,
    }

    log_file = Path("experiment_log.jsonl")
    with log_file.open("a") as f:
        f.write(json.dumps(log_entry) + "\n")

if __name__ == "__main__":
    results = evaluate_model()
    print("Evaluation Results:")
    for k, v in results.items():
        print(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}")


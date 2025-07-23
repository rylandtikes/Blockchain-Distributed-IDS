import os
import torch
from collections import Counter
import torch.nn as nn
import evaluate_model
import json
from datetime import datetime
import numpy as np

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from prepare_data import prepare_dataset

# Prevent TensorFlow import by Hugging Face
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TF"] = "0"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Compute class weights for imbalanced datasets
def get_class_weights(labels):
    counts = Counter(labels)
    total = sum(counts.values())
    weight_0 = total / (2 * counts[0])
    weight_1 = total / (2 * counts[1]) * 1.3 
    return torch.tensor([weight_0, weight_1], dtype=torch.float).to(device)

# Focal Loss implementation
class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2, weight=None, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.weight = weight
        self.reduction = reduction

    def forward(self, logits, targets):
        ce_loss = nn.CrossEntropyLoss(weight=self.weight, reduction='none')(logits, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss

# Custom Trainer with Focal Loss
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        loss_fct = FocalLoss(weight=self.class_weights)
        loss = loss_fct(logits, labels)

        return (loss, outputs) if return_outputs else loss

# Hyperparameter and threshold sweep
HYPERPARAMS = [
    {'batch_size': 32, 'lr': 1e-5, 'epochs': 10, 'weight_1': 2.0, 'weight_decay': 0.05},
    {'batch_size': 64, 'lr': 2e-5, 'epochs': 15, 'weight_1': 2.5, 'weight_decay': 0.1},
    {'batch_size': 128, 'lr': 3e-5, 'epochs': 8, 'weight_1': 3.0, 'weight_decay': 0.2},
]
THRESHOLDS = np.arange(0.3, 0.7, 0.05)

def train():
    dataset = prepare_dataset()
    train_labels = dataset["train"]["label"]
    best_f1 = 0
    best_config = None
    best_results = None
    for params in HYPERPARAMS:
        class_weights = get_class_weights(train_labels)
        class_weights[1] = class_weights[1] * params['weight_1']
        training_args = TrainingArguments(
            output_dir=f"./bert-mini-hdfs-results-bs{params['batch_size']}-lr{params['lr']}-w{params['weight_1']}-wd{params['weight_decay']}",
            eval_strategy="epoch",
            save_strategy="epoch",
            learning_rate=params['lr'],
            per_device_train_batch_size=params['batch_size'],
            per_device_eval_batch_size=params['batch_size'],
            num_train_epochs=params['epochs'],
            weight_decay=params['weight_decay'],
            logging_dir="./logs",
            logging_steps=50,
            save_total_limit=2,
            fp16=torch.cuda.is_available(),
            dataloader_num_workers=4,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            warmup_steps=200,
            lr_scheduler_type="cosine"
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            "prajjwal1/bert-mini", num_labels=2
        ).to(device)
        tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-mini")
        trainer = WeightedTrainer(
            model=model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["test"],
            tokenizer=tokenizer,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
        )
        trainer.class_weights = class_weights
        trainer.train()
        trainer.save_model(training_args.output_dir)
        # Threshold sweep
        for threshold in THRESHOLDS:
            results = evaluate_model.evaluate_model(model_dir=training_args.output_dir, threshold=threshold)
            log_path = os.path.join(os.path.dirname(__file__), "training_log.json")
            with open(log_path, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "model": "prajjwal1/bert-mini",
                    "epochs": params['epochs'],
                    "train_batch_size": params['batch_size'],
                    "learning_rate": params['lr'],
                    "class_weight_1": params['weight_1'],
                    "weight_decay": params['weight_decay'],
                    "threshold": threshold,
                    **results
                }) + "\n")
            if results.get("f1", 0) > best_f1:
                best_f1 = results["f1"]
                best_config = {**params, "threshold": threshold}
                best_results = results
                best_model_dir = training_args.output_dir
    
    # Save the best model to a dedicated directory
    if best_config:
        import shutil
        best_model_save_path = "./bert-mini-hdfs-best"
        if os.path.exists(best_model_save_path):
            shutil.rmtree(best_model_save_path)
        shutil.copytree(best_model_dir, best_model_save_path)
        print(f"Best model saved to: {best_model_save_path}")
    
    print("Best config:", best_config)
    print("Best results:", best_results)

if __name__ == "__main__":
    train()


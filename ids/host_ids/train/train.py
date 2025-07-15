import os
import torch
from collections import Counter
import torch.nn as nn
import evaluate_model
import json
from datetime import datetime

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    TrainingArguments,
    Trainer
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

# Custom Trainer with weighted loss
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")

        loss_fct = nn.CrossEntropyLoss(weight=self.class_weights)
        loss = loss_fct(logits, labels)

        return (loss, outputs) if return_outputs else loss

def train():
    dataset = prepare_dataset()

    # Load model and tokenizer
    model = AutoModelForSequenceClassification.from_pretrained(
        "prajjwal1/bert-mini", num_labels=2
    ).to(device)

    tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-mini")

    # Compute class weights
    train_labels = dataset["train"]["label"]
    class_weights = get_class_weights(train_labels)

    training_args = TrainingArguments(
        output_dir="./bert-mini-hdfs-results",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=3e-5,
        per_device_train_batch_size=64,
        per_device_eval_batch_size=64,
        num_train_epochs=15,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=50,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),  # Only enable if GPU is available
        dataloader_num_workers=4,  # Reasonable default for CPUs
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        warmup_steps=200,
        lr_scheduler_type="cosine"
    )

    trainer = WeightedTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer
    )
    trainer.class_weights = class_weights  # Inject weights into trainer

    trainer.train()
    trainer.save_model("bert-mini-hdfs")

    # Run evaluation
    results = evaluate_model.evaluate_model(model_dir="bert-mini-hdfs")

    # Append to log file
    log_path = os.path.join(os.path.dirname(__file__), "training_log.json")
    with open(log_path, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "model": "prajjwal1/bert-mini",
            "epochs": training_args.num_train_epochs,
            "train_batch_size": training_args.per_device_train_batch_size,
            "learning_rate": training_args.learning_rate,
            **results
        }) + "\n")

if __name__ == "__main__":
    train()


import os
os.environ["TRANSFORMERS_NO_TF"] = "1"  # <-- Must be set before transformers is imported

from transformers import pipeline
import yaml

config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

model_path = config["model_path"]
alert_threshold = config["alert_threshold"]

classifier = pipeline("text-classification", model=model_path, framework="pt")

def classify_log_line(log_line):
    result = classifier(log_line, truncation=True, max_length=128)[0]
    label = result['label']
    score = result['score']
    return label, score

if __name__ == "__main__":
    print("Device set to use cpu")
    test_line = "Error: BlockManager failed to remove block"
    label, score = classify_log_line(test_line)
    print(f"Log line classified as: {label} with score: {score:.4f}")


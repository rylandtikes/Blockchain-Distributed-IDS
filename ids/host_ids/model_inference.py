from transformers import pipeline
import yaml
import os

config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)


classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

def classify_log_line(log_line):
    result = classifier(log_line, truncation=True)[0]
    label = result['label']  # 'POSITIVE' or 'NEGATIVE'
    score = result['score']
    return label, score

'''
def classify_log_line(log_line):
    if "Failed password" in log_line:
        return "LABEL_1", 0.95  # Simulated high confidence
    return "LABEL_0", 0.1
'''


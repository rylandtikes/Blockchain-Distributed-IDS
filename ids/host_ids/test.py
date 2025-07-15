import os
os.environ["USE_TF"] = "0"

from transformers import pipeline

classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
print(classifier("Failed password for root from 192.168.1.100 port 22 ssh2"))


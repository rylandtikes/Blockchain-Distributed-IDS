from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="distilbert-hdfs",
    tokenizer="distilbert-hdfs"
)

log_line = "Received block blk_12345678_0 of size 67108864 from datanode"
result = classifier(log_line)
print(result)


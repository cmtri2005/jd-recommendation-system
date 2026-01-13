import json

with open("evaluation/dataset/golden_dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(len(data))

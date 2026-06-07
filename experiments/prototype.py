import torch
from transformers import AutoTokenizer, AutoModel

print("Loading CodeBERT model... Please wait.")

model_name = "microsoft/codebert-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

print("Model loaded successfully!")


sample_code = """
def calculate_experience(repo_data):
    stars = repo_data.get('stars', 0)
    commits = repo_data.get('commits', 0)
    return (stars * 10) + commits
"""

print(f"\nAnalyzing Sample Code Snippet:\n{sample_code}")


inputs = tokenizer(sample_code, return_tensors="pt", padding=True, truncation=True)

# 4. Generating Embeddings
with torch.no_grad():
    outputs = model(**inputs)

# 5. Extracting Vector (Last hidden state)
embeddings = outputs.last_hidden_state

print("\nAI Pipeline Success!")
print(f"Vector Shape: {embeddings.shape}")
print("Meaning: CodeBERT successfully converted your code into heavy AI numbers!")


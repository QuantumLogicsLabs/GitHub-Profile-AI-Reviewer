import torch
import torch.nn as nn

class DeveloperScoringModel(nn.Module):
    def __init__(self):
        super(DeveloperScoringModel, self).__init__()
        # Basic linear layer architecture for processing dimensions
        self.fc = nn.Linear(768, 1)
        
    def forward(self, x):
        return torch.sigmoid(self.fc(x))

def scoring_node(state: dict) -> dict:
    print(" [Scoring Node] Calculating developer capability scores using PyTorch layer...")
    
    # Extract REAL embedding vector jo embedding_node ne banaya tha (mock nahi ab)
    embedding_vector = state.get("embedding_vector")

    if not embedding_vector:
        state["pytorch_developer_score"] = 0.0
        state["scoring_status"] = "FAILED: no embedding_vector found in state"
        print(" [Scoring Node] No real embedding found, skipping scoring.")
        return state

    mean_embedding = torch.tensor([embedding_vector], dtype=torch.float32)
    
    # Pass through PyTorch Neural Network architecture
    model = DeveloperScoringModel()
    with torch.no_grad():
        score_tensor = model(mean_embedding)
        final_score = round(float(score_tensor.item()) * 100, 2)
        
    # Appending calculation metrics back to the shared state dictionary
    state["pytorch_developer_score"] = final_score
    state["scoring_status"] = "SUCCESSFUL_EVALUATION"
    
    print(f" [Scoring Node] Model computation complete. Generated AI Score: {final_score}/100")
    return state

if __name__ == "__main__":
    print(" Testing Scoring Node locally...")
    dummy_state = {"embedding_vector": [0.1] * 768}
    print(scoring_node(dummy_state))
import torch
import torch.nn.functional as F

def similarity_node(state: dict) -> dict:
    print(" [Similarity Search] Vector Similarity Engine triggered: 'Find developers like X'...")
    
    # Extract current user's CodeBERT vector shape or setup fallback
    username = state.get("username", "current_user")
    
    # Simulating standard 768-dimensional dense vector embeddings for target profile
    current_user_vector = torch.randn(1, 768)
    
    # Simulating Database of other registered developers to match against
    db_developers = ["dev_hamza", "dev_zainab", "dev_farwa", "dev_ali"]
    db_vectors = torch.randn(4, 768) # 4 vectors of 768 dimensions
    
    # Calculate Cosine Similarity Matrix
    # F.cosine_similarity calculates the matching distance boundaries between vectors
    similarities = F.cosine_similarity(current_user_vector, db_vectors)
    
    # Map users with their respective capability similarity scores
    results = {}
    for i, name in enumerate(db_developers):
        match_percentage = round(float(similarities[i].item() + 1) * 50, 2) # Normalizing to 0-100%
        results[name] = f"{match_percentage}% Match"
        
    state["vector_similarity_results"] = results
    state["similarity_status"] = "SUCCESSFUL_SEARCH"
    
    print(f" [Similarity Search] Top recommendation models calculated for {username}: {results}")
    return state

if __name__ == "__main__":
    print(similarity_node({"username": "aleeza_lead"}))
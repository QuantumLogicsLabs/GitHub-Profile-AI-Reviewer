import torch
from transformers import AutoTokenizer, AutoModel

# Global level variables taake nodes call hone par model baar-baar download/load na ho (Optimization)
TOKENIZER = None
MODEL = None

def get_codebert_model():
    global TOKENIZER, MODEL
    if TOKENIZER is None or MODEL is None:
        print(" Loading CodeBERT pipeline into runtime architecture...")
        TOKENIZER = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        MODEL = AutoModel.from_pretrained("microsoft/codebert-base")
    return TOKENIZER, MODEL

def embedding_node(state: dict) -> dict:
    """
    LangGraph Node to process code text inputs into heavy mathematical vector embeddings.
    Accepts state and appends raw tensor shape information for downstream routing evaluation.
    """
    print(" [Embedding Node] Initializing CodeBERT processor vector generation...")
    
    # 1. Core sample input snippet inside code matrix (Dynamic fallback handle)
    sample_code = state.get("code_snippet", """
def calculate_experience(repo_data):
    stars = repo_data.get('stars', 0)
    commits = repo_data.get('commits', 0)
    return (stars * 10) + commits
    """)

    try:
        # 2. Loading weights securely
        tokenizer, model = get_codebert_model()

        # 3. Transforming code text into deep tensor arrays
        code_tokens = tokenizer.tokenize(sample_code)
        tokens_ids = tokenizer.convert_tokens_to_ids(code_tokens)
        context_embeddings = model(torch.tensor([tokens_ids]))[0]

        # 4. Extracting structural metadata to return into graph state space
        vector_shape = list(context_embeddings.shape)
        
        state["embedding_vector_shape"] = vector_shape
        state["embedding_status"] = "SUCCESS"
        print(f" [Embedding Node] Successfully created code dimensions vector: {vector_shape}")

    except Exception as e:
        state["embedding_status"] = f"FAILED: {str(e)}"
        state["embedding_vector_shape"] = []
        print(f" [Embedding Node] Core evaluation error: {str(e)}")

    # 5. Return updated state to pipeline structure
    return state


# ---- Dynamic Dummy Execution Box for Verification ----
if __name__ == "__main__":
    initial_state = {"username": "test_user", "code_snippet": "print('Hello LangGraph World')"}
    print(" Testing Embedding Node locally with dummy state input...")
    final_state = embedding_node(initial_state)
    print(f"Final State Output Keys: {list(final_state.keys())}\n")
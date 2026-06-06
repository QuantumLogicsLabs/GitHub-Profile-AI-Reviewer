import sys
import os
# Auto-injecting path patch for root module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph.graph import StateGraph, END
from typing import Dict, Any

# 1. Importing all functional pipeline nodes (Including new AI/ML nodes)
from backend.graph.nodes.github_node import github_node
from backend.graph.nodes.embedding_node import embedding_node
from backend.graph.nodes.scoring_node import scoring_node
from backend.graph.nodes.starcoder_node import starcoder_node
from backend.graph.nodes.similarity_node import similarity_node

# 2. Initialize LangGraph StateGraph Architecture
workflow = StateGraph(dict)

# 3. Injecting all pipeline operational nodes into the workflow
workflow.add_node("fetch_github_metrics", github_node)
workflow.add_node("generate_codebert_vectors", embedding_node)
workflow.add_node("calculate_pytorch_scores", scoring_node)
workflow.add_node("evaluate_starcoder_quality", starcoder_node)
workflow.add_node("vector_similarity_search", similarity_node)

# 4. Setting Up Execution Routing Map Entry Point
workflow.set_entry_point("fetch_github_metrics")

# Full Master AI Pipeline Routing Diagram:
# GitHub API -> CodeBERT -> Fine-Tuned PyTorch -> StarCoder Quality -> Vector Search -> End
workflow.add_edge("fetch_github_metrics", "generate_codebert_vectors")
workflow.add_edge("generate_codebert_vectors", "calculate_pytorch_scores")
workflow.add_edge("calculate_pytorch_scores", "evaluate_starcoder_quality")
workflow.add_edge("evaluate_starcoder_quality", "vector_similarity_search")
workflow.add_edge("vector_similarity_search", END)

# 5. Compile the Final Unified Executive App System
app = workflow.compile()


# ---- Local Master Pipeline Integration Validation ----
if __name__ == "__main__":
    print(" [System Integration] Running Full Master LangGraph Compiled Pipeline...")
    
    # Standard Shared Input State Initialization
    dummy_input_state = {
        "username": "sp25-bai-047-wq",  
        "code_snippet": "def verify_leader(): return True"
    }
    
    # Execute full unified pipeline orchestration sequence
    final_output_state = app.invoke(dummy_input_state)
    
    print("\n ===================================================")
    print(" MASTER AI PIPELINE EXECUTION SUCCESSFUL (100% DONE) ")
    print("=======================================================")
    print(f" Final Global State Resulting Keys: {list(final_output_state.keys())}\n")
    print(f" Extracted Fine-Tuned PyTorch AI Score: {final_output_state.get('pytorch_developer_score')}/100")
    print(f" StarCoder Assessment: {final_output_state.get('starcoder_quality_metrics', {}).get('starcoder_recommendation')}")
    print(f" Vector Similarity Matches: {final_output_state.get('vector_similarity_results')}\n")
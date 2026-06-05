import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from langgraph.graph import StateGraph, END
from typing import Dict, Any

# 1. Importing all functional pipeline nodes
from backend.graph.nodes.github_node import github_node
from backend.graph.nodes.embedding_node import embedding_node
from backend.graph.nodes.scoring_node import scoring_node
from backend.graph.nodes.starcoder_node import starcoder_node

# 2. Initialize LangGraph StateGraph Architecture
workflow = StateGraph(dict)

# 3. Injecting all pipeline operational nodes
workflow.add_node("fetch_github_metrics", github_node)
workflow.add_node("generate_codebert_vectors", embedding_node)
workflow.add_node("calculate_pytorch_scores", scoring_node)
workflow.add_node("evaluate_starcoder_quality", starcoder_node)

# 4. Setting Up Execution Routing Map
workflow.set_entry_point("fetch_github_metrics")

# Full Pipeline Blueprint: Github API -> CodeBERT Embeddings -> PyTorch Scoring Engine -> StarCoder Metrics -> End
workflow.add_edge("fetch_github_metrics", "generate_codebert_vectors")
workflow.add_edge("generate_codebert_vectors", "calculate_pytorch_scores")
workflow.add_edge("calculate_pytorch_scores", "evaluate_starcoder_quality")
workflow.add_edge("evaluate_starcoder_quality", END)

# 5. Compile the Final Executive App System
app = workflow.compile()


# ---- Local Pipeline Integration Validation ----
if __name__ == "__main__":
    print(" [System Integration] Running Full LangGraph Compiled Pipeline...")
    
    # Standard Shared Input State Initialization
    dummy_input_state = {
        "username": "lead_aleeza_profile",
        "code_snippet": "def verify_leader(): return True"
    }
    
    # Execute full unified pipeline orchestration
    final_output_state = app.invoke(dummy_input_state)
    
    print("\n👑 ===================================================")
    print(" FINAL PIPELINE EXECUTION SUCCESSFUL (100% COMPLETE) ")
    print("=======================================================")
    print(f" Final Resulting Keys inside State: {list(final_output_state.keys())}\n")
    print(f" Extracted PyTorch AI Score: {final_output_state.get('pytorch_developer_score')}/100")
    print(f" StarCoder Assessment: {final_output_state.get('starcoder_quality_metrics', {}).get('starcoder_recommendation')}")
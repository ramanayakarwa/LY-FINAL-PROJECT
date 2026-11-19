from typing import Dict


def build_final_recommendation(agent_output: Dict, security_output: Dict) -> Dict:
    priority = agent_output.get("priority", "LOW")
    action = agent_output.get("recommended_action", "Continue monitoring.")
    treatment = agent_output.get("unique_recommendation", "Maintain current conditions.")

    if not security_output.get("allow_action", False):
        action = "BLOCK_AUTOMATION_AND_REQUEST_HUMAN_REVIEW"
        treatment = "Action blocked by cybersecurity layer due to unsafe or suspicious conditions."

    return {
        "priority": priority,
        "action": action,
        "treatment": treatment,
        "security_status": security_output.get("security_status", "SAFE")
    }
from app.services.state_service import record_action


def execute_simulated(
    action: str,
    parameters: dict,
    gate_result: dict,
) -> dict:

    if gate_result["decision"] != "ALLOW":

        result = {
            "action": action,
            "execution": "NOT_EXECUTED",
            "mode": "SIMULATION",
            "gate": gate_result["decision"],
        }

    else:

        result = {
            "action": action,
            "execution": "SIMULATED",
            "mode": "SIMULATION",
            "parameters": parameters,
        }

    record_action(result)

    return result
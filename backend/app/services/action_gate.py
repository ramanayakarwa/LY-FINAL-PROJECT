import os

from app.services.safety_service import check_safety


class ActionGate:

    def __init__(self, security_result=None):

        self.security = security_result or {
            "decision": "BLOCK",
            "alerts": ["Security not evaluated"],
        }

    def evaluate(
        self,
        action: str,
        parameters: dict | None = None,
    ) -> dict:

        parameters = parameters or {}

        # Emergency commands

        if action in ("STOP", "HALT"):
            return {
                "decision": "ALLOW",
                "action": action,
                "reason": "Emergency stop is permitted",
                "alerts": [],
            }

        # Cybersecurity verification

        security_decision = self.security.get(
            "decision",
            "BLOCK",
        )

        if security_decision != "ALLOW":
            return {
                "decision": (
                    "HALT"
                    if security_decision == "HALT"
                    else "BLOCK"
                ),
                "action": action,
                "reason": "Cybersecurity validation failed",
                "alerts": self.security.get("alerts", []),
            }

        # Physical safety verification

        safety_decision, alerts = check_safety(
            action,
            parameters,
        )

        if safety_decision != "ALLOW":
            return {
                "decision": safety_decision,
                "action": action,
                "reason": "Physical safety validation failed",
                "alerts": alerts,
            }

        # Hardware commands are not enabled yet.

        demo_mode = (
            os.getenv("ARES_DEMO_MODE", "true").lower()
            == "true"
        )

        if not demo_mode:
            return {
                "decision": "BLOCK",
                "action": action,
                "reason": (
                    "Physical ESP32 actuator integration "
                    "has not been commissioned"
                ),
                "alerts": ["HARDWARE_NOT_COMMISSIONED"],
            }

        return {
            "decision": "ALLOW",
            "action": action,
            "reason": (
                "Approved for software simulation only"
            ),
            "alerts": [],
        }
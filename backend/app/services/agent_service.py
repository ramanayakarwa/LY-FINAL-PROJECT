class AgenticLayer:

    def __init__(self, data: dict, security=None):
        self.data = data
        self.security = security or {}

    def final_agentic_output(self):

        # 1. Cybersecurity first

        security_decision = self.security.get("decision")

        if security_decision in ("BLOCK", "HALT"):
            return self._response(
                priority="HIGH",
                action="INSPECT_SENSORS",
                reason=(
                    "Security validation failed. "
                    "Automatic intervention is not permitted."
                ),
                precautions=[
                    "Check sensors and communication.",
                    "Do not actuate using untrusted data.",
                ],
            )

        crop = str(
            self.data.get("crop") or "Unknown"
        )

        disease = str(
            self.data.get("disease") or ""
        ).lower().strip()

        try:
            confidence = float(
                self.data.get("confidence") or 0
            )
        except (ValueError, TypeError):
            confidence = 0

        # 2. Disease detection

        is_disease = (
            bool(disease)
            and "healthy" not in disease
            and "unknown" not in disease
        )

        if is_disease and confidence >= 0.80:

            return self._response(
                priority="HIGH",
                action="INSPECT_AFFECTED_LEAF",
                reason=(
                    f"Possible {disease} detected on {crop}. "
                    f"Confidence: {confidence:.1%}"
                ),
                precautions=[
                    "Capture photographs from different angles.",
                    "Verify the diagnosis.",
                    "Identify the exact affected leaf.",
                    "Do not remove a leaf until its position "
                    "and the arm movement are verified.",
                    "Do not automatically apply chemicals.",
                ],
            )

        # 3. Low-confidence classification

        if is_disease and confidence < 0.80:

            return self._response(
                priority="MEDIUM",
                action="RECAPTURE_IMAGES",
                reason=(
                    "The disease prediction has low confidence."
                ),
                precautions=[
                    "Take additional photographs.",
                    "Use good lighting.",
                    "Do not remove leaves based on "
                    "an uncertain prediction.",
                ],
            )

        # 4. Soil moisture

        try:
            moisture = float(
                self.data.get("soil_moisture")
            )
        except (ValueError, TypeError):
            moisture = None

        if moisture is not None and moisture < 30:

            return self._response(
                priority="MEDIUM",
                action="REQUEST_WATERING_REVIEW",
                reason=(
                    f"Soil moisture is {moisture:.1f}%, "
                    "below the demonstration threshold."
                ),
                precautions=[
                    "Verify the soil moisture sensor.",
                    "Confirm which plant needs water.",
                    "Check the water tank and pump.",
                    "Avoid excessive watering.",
                ],
            )

        # 5. Temperature

        try:
            temperature = float(
                self.data.get("temperature")
            )
        except (ValueError, TypeError):
            temperature = None

        if (
            temperature is not None
            and temperature > 38
        ):

            return self._response(
                priority="MEDIUM",
                action="INSPECT_HEAT_STRESS",
                reason=(
                    f"High temperature detected: "
                    f"{temperature:.1f} C"
                ),
                precautions=[
                    "Verify the temperature reading.",
                    "Inspect plants for heat stress.",
                    "Check soil moisture.",
                ],
            )

        # 6. Normal monitoring

        return self._response(
            priority="LOW",
            action="MONITOR",
            reason=(
                "No urgent issue found in "
                "the available observations."
            ),
            precautions=[
                "Continue monitoring plant conditions.",
            ],
        )

    @staticmethod
    def _response(
        priority,
        action,
        reason,
        precautions,
    ):
        return {
            "priority": priority,
            "action": action,
            "reason": reason,
            "precautions": precautions,
            "requires_gate": True,
            "execution_status": "PROPOSAL_ONLY",
            "agent_type": "RULE_BASED",
        }
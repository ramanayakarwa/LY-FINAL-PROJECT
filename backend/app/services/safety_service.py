from app.services.state_service import snapshot


MOVEMENT_ACTIONS = {
    "MOVE_FORWARD",
    "MOVE_BACKWARD",
    "TURN_LEFT",
    "TURN_RIGHT",
}

PHYSICAL_ACTIONS = MOVEMENT_ACTIONS | {
    "WATER_PLANT",
    "SPRAY_WATER",
    "GRIP_LEAF",
    "ARM_HOME",
}


def check_safety(
    action: str,
    parameters: dict,
) -> tuple[str, list[str]]:

    # Stop must always be possible.
    if action in ("STOP", "HALT"):
        return "ALLOW", []

    if action not in PHYSICAL_ACTIONS:
        return "BLOCK", ["Unsupported physical action"]

    state = snapshot()

    if not state["fresh"]:
        return "HALT", ["No fresh sensor telemetry"]

    if (
        not state["verified"]
        and state["source"] != "SIMULATION"
    ):
        return "BLOCK", ["Sensor source is unverified"]

    data = state["data"]
    alerts = []

    battery = data.get("battery_percent")

    if battery is None or battery < 15:
        alerts.append("Battery missing or critically low")

    if data.get("obstacle_stop") is True:
        alerts.append("Obstacle emergency interlock active")

    # Rover movement checks

    if action in MOVEMENT_ACTIONS:

        distance = data.get("distance_cm")

        if distance is None or distance < 30:
            alerts.append(
                "Obstacle too close or distance unknown"
            )

        try:
            speed = float(
                parameters.get("speed_percent", 0)
            )
            duration = float(
                parameters.get("duration_s", 0)
            )

            if not (0 < speed <= 40):
                alerts.append("Unsafe speed")

            if not (0 < duration <= 3):
                alerts.append("Unsafe movement duration")

        except (ValueError, TypeError):
            alerts.append("Invalid movement parameters")

    # Watering and arm checks

    if action in {
        "WATER_PLANT",
        "SPRAY_WATER",
        "GRIP_LEAF",
    }:

        if parameters.get("manual_confirmed") is not True:
            alerts.append("Operator confirmation required")

        if parameters.get("target_verified") is not True:
            alerts.append("Target verification required")

        if data.get("arm_homed") is not True:
            alerts.append("Arm home position not verified")

    if action == "WATER_PLANT":

        plant_id = str(
            parameters.get("plant_id", "")
        ).strip()

        if not plant_id:
            alerts.append("Plant ID required")

        moisture = data.get("soil_moisture")

        if moisture is None or moisture >= 30:
            alerts.append(
                "No verified low-moisture condition"
            )

    if action in {
        "WATER_PLANT",
        "SPRAY_WATER",
    }:

        try:
            duration = float(
                parameters.get("duration_s", 0)
            )

            if not (0 < duration <= 3):
                alerts.append("Unsafe pump duration")

        except (ValueError, TypeError):
            alerts.append("Invalid pump duration")

    if action == "GRIP_LEAF":
        alerts.append(
            "Leaf localization and robotic arm "
            "calibration not yet validated"
        )

    if alerts:
        return "HALT", alerts

    return "ALLOW", []
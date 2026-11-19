HIGH_VALUE_CROPS = {
    "grapes",
    "pomegranate",
    "mango",
    "cotton",
    "coffee",
    "coconut",
    "banana",
    "orange",
    "papaya"
}


def get_high_value_status(crop_name: str) -> dict:
    crop = crop_name.strip().lower()

    if crop in HIGH_VALUE_CROPS:
        return {
            "high_value_crop": True,
            "priority_monitoring": "High"
        }

    return {
        "high_value_crop": False,
        "priority_monitoring": "Normal"
    }
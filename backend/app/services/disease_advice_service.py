def get_disease_advice(raw_label: str) -> dict:
    advice_map = {
        "Potato___Late_blight": {
            "health_status": "Needs Attention",
            "treatment": "Apply a suitable fungicide such as Metalaxyl-based treatment and isolate infected plants.",
            "precautions": [
                "Avoid excess leaf wetness.",
                "Remove infected leaves immediately.",
                "Do not overcrowd plants."
            ],
            "prevention": [
                "Ensure proper air circulation.",
                "Use disease-free seed material.",
                "Inspect plants regularly."
            ]
        },
        "Potato___Early_blight": {
            "health_status": "Needs Attention",
            "treatment": "Apply recommended fungicide and remove infected foliage.",
            "precautions": [
                "Avoid water stress.",
                "Remove fallen infected leaves.",
                "Maintain balanced soil nutrition."
            ],
            "prevention": [
                "Use crop rotation.",
                "Monitor lower leaves regularly.",
                "Avoid overhead irrigation late in the day."
            ]
        },
        "Tomato___Early_blight": {
            "health_status": "Needs Attention",
            "treatment": "Use fungicide spray and prune infected leaves.",
            "precautions": [
                "Do not splash water on leaves.",
                "Discard infected leaves safely.",
                "Keep soil well drained."
            ],
            "prevention": [
                "Use resistant varieties where possible.",
                "Maintain spacing between plants.",
                "Monitor humidity conditions."
            ]
        },
        "Tomato___Late_blight": {
            "health_status": "Critical",
            "treatment": "Apply anti-blight fungicide immediately and isolate infected plants.",
            "precautions": [
                "Avoid leaf wetness.",
                "Do not mix infected and healthy plants.",
                "Remove severely infected parts."
            ],
            "prevention": [
                "Inspect crop after rainfall.",
                "Improve airflow.",
                "Use preventive fungicide in high-risk conditions."
            ]
        },
        "Tomato___Leaf_Mold": {
            "health_status": "Needs Attention",
            "treatment": "Apply fungicide and reduce humidity around the crop.",
            "precautions": [
                "Avoid excessive greenhouse humidity.",
                "Do not overwater.",
                "Remove infected leaves."
            ],
            "prevention": [
                "Ensure ventilation.",
                "Keep foliage dry.",
                "Sanitize tools and plant area."
            ]
        },
        "Tomato___healthy": {
            "health_status": "Healthy",
            "treatment": "No treatment required.",
            "precautions": [
                "Maintain current irrigation and nutrient balance."
            ],
            "prevention": [
                "Continue routine monitoring.",
                "Keep plants clean and well ventilated."
            ]
        },
        "Potato___healthy": {
            "health_status": "Healthy",
            "treatment": "No treatment required.",
            "precautions": [
                "Maintain current field conditions."
            ],
            "prevention": [
                "Continue regular inspection.",
                "Avoid waterlogging."
            ]
        },
        "Pepper__bell___Bacterial_spot": {
            "health_status": "Needs Attention",
            "treatment": "Apply copper-based antibacterial treatment and remove infected leaves.",
            "precautions": [
                "Avoid overhead irrigation.",
                "Disinfect tools after use.",
                "Do not handle wet plants excessively."
            ],
            "prevention": [
                "Use clean planting material.",
                "Maintain spacing.",
                "Monitor leaf spots early."
            ]
        },
        "Pepper__bell___healthy": {
            "health_status": "Healthy",
            "treatment": "No treatment required.",
            "precautions": [
                "Maintain balanced watering and nutrition."
            ],
            "prevention": [
                "Continue regular crop monitoring."
            ]
        },
    }

    default_advice = {
        "health_status": "Needs Review",
        "treatment": "Consult agricultural expert or verify prediction before applying treatment.",
        "precautions": [
            "Inspect the crop manually.",
            "Avoid unnecessary chemical application."
        ],
        "prevention": [
            "Continue monitoring the crop regularly."
        ]
    }

    return advice_map.get(raw_label, default_advice)
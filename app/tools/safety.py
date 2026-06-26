UNSAFE_MEDICAL_PATTERNS = [
    "diagnose",
    "diagnosis",
    "what disease",
    "what condition do i have",
    "prescribe",
    "prescription for",
    "change dosage",
    "increase dose",
    "decrease dose",
    "double the dose",
    "stop taking",
    "replace your doctor",
    "instead of medication",
    "instead of seeing a doctor",
    "emergency treatment",
    "chest pain what should",
    "suicide",
    "overdose intentionally",
]

REFUSAL_CATEGORIES = {
    "diagnosis": [
        "diagnose", "diagnosis", "what disease", "what condition do i have",
    ],
    "prescription": ["prescribe", "prescription for"],
    "dosage": [
        "change dosage", "increase dose", "decrease dose", "double the dose",
    ],
    "emergency": ["emergency treatment", "chest pain what should", "overdose"],
}


def classify_safety_violation(message: str) -> str | None:
    lowered = message.lower()
    for category, patterns in REFUSAL_CATEGORIES.items():
        if any(p in lowered for p in patterns):
            return category
    if any(p in lowered for p in UNSAFE_MEDICAL_PATTERNS):
        return "general"
    return None


def is_unsafe_medical_advice(message: str) -> bool:
    return classify_safety_violation(message) is not None


def safety_response(category: str | None = None) -> str:
    responses = {
        "diagnosis": (
            "I cannot diagnose medical conditions. MediGuardian helps you "
            "organize medications — not replace clinical judgment. Please "
            "consult a licensed healthcare provider for diagnosis."
        ),
        "prescription": (
            "I cannot prescribe medications. Only qualified prescribers can "
            "issue prescriptions. I can help you track medications already "
            "prescribed by your doctor."
        ),
        "dosage": (
            "I cannot recommend dosage changes. Altering medication doses "
            "without medical supervision can be dangerous. Please speak "
            "with your doctor or pharmacist."
        ),
        "emergency": (
            "This sounds like a medical emergency. Please call emergency "
            "services immediately (911 or your local number). MediGuardian "
            "is not an emergency service."
        ),
        "general": (
            "I cannot provide medical diagnosis, change dosages, or replace "
            "professional healthcare advice. Please consult your doctor or "
            "pharmacist for medical decisions."
        ),
    }
    return responses.get(category or "general", responses["general"])

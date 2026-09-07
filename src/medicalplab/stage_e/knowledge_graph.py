"""Lightweight medical knowledge graph and static curriculum taxonomy for Stage-E.

Defines clinical domain hierarchies, topic prerequisite dependencies, and related subject paths.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicNode:
    topic: str
    category: str
    prerequisites: tuple[str, ...]
    related_topics: tuple[str, ...]
    default_difficulty: str = "medium"


STATIC_TAXONOMY: dict[str, TopicNode] = {
    # --- Cardiology ---
    "cardiovascular physiology": TopicNode(
        topic="Cardiovascular Physiology",
        category="Cardiology",
        prerequisites=(),
        related_topics=("Hypertension", "Heart Failure"),
        default_difficulty="easy",
    ),
    "hypertension": TopicNode(
        topic="Hypertension",
        category="Cardiology",
        prerequisites=("Cardiovascular Physiology",),
        related_topics=("Hypertension Management", "Cardiovascular Risk Assessment"),
        default_difficulty="easy",
    ),
    "hypertension management": TopicNode(
        topic="Hypertension Management",
        category="Cardiology",
        prerequisites=("Hypertension", "Cardiovascular Physiology"),
        related_topics=("Heart Failure", "Chronic Kidney Disease"),
        default_difficulty="medium",
    ),
    "heart failure": TopicNode(
        topic="Heart Failure",
        category="Cardiology",
        prerequisites=("Cardiovascular Physiology", "Hypertension"),
        related_topics=("Hypertension Management", "Acute Coronary Syndrome"),
        default_difficulty="medium",
    ),
    "acute coronary syndrome": TopicNode(
        topic="Acute Coronary Syndrome",
        category="Cardiology",
        prerequisites=("Cardiovascular Physiology",),
        related_topics=("Arrhythmias", "Heart Failure"),
        default_difficulty="hard",
    ),
    "arrhythmias": TopicNode(
        topic="Arrhythmias",
        category="Cardiology",
        prerequisites=("Cardiovascular Physiology",),
        related_topics=("Acute Coronary Syndrome", "Heart Failure"),
        default_difficulty="hard",
    ),

    # --- Endocrinology ---
    "endocrine physiology": TopicNode(
        topic="Endocrine Physiology",
        category="Endocrinology",
        prerequisites=(),
        related_topics=("Diabetes Mellitus", "Thyroid Disorders"),
        default_difficulty="easy",
    ),
    "diabetes mellitus": TopicNode(
        topic="Diabetes Mellitus",
        category="Endocrinology",
        prerequisites=("Endocrine Physiology",),
        related_topics=("Diabetic Ketoacidosis", "Cardiovascular Risk Assessment"),
        default_difficulty="medium",
    ),
    "diabetic ketoacidosis": TopicNode(
        topic="Diabetic Ketoacidosis",
        category="Endocrinology",
        prerequisites=("Diabetes Mellitus", "Endocrine Physiology"),
        related_topics=("Fluid and Electrolytes",),
        default_difficulty="hard",
    ),
    "thyroid disorders": TopicNode(
        topic="Thyroid Disorders",
        category="Endocrinology",
        prerequisites=("Endocrine Physiology",),
        related_topics=("Diabetes Mellitus",),
        default_difficulty="medium",
    ),

    # --- Respiratory ---
    "respiratory physiology": TopicNode(
        topic="Respiratory Physiology",
        category="Respiratory",
        prerequisites=(),
        related_topics=("Asthma", "COPD"),
        default_difficulty="easy",
    ),
    "asthma": TopicNode(
        topic="Asthma",
        category="Respiratory",
        prerequisites=("Respiratory Physiology",),
        related_topics=("COPD", "Pneumonia"),
        default_difficulty="medium",
    ),
    "copd": TopicNode(
        topic="COPD",
        category="Respiratory",
        prerequisites=("Respiratory Physiology",),
        related_topics=("Asthma", "Pneumonia"),
        default_difficulty="medium",
    ),
    "pneumonia": TopicNode(
        topic="Pneumonia",
        category="Respiratory",
        prerequisites=("Respiratory Physiology",),
        related_topics=("COPD", "Asthma"),
        default_difficulty="medium",
    ),

    # --- Nephrology ---
    "renal physiology": TopicNode(
        topic="Renal Physiology",
        category="Nephrology",
        prerequisites=(),
        related_topics=("Acute Kidney Injury", "Chronic Kidney Disease"),
        default_difficulty="easy",
    ),
    "acute kidney injury": TopicNode(
        topic="Acute Kidney Injury",
        category="Nephrology",
        prerequisites=("Renal Physiology",),
        related_topics=("Chronic Kidney Disease", "Fluid and Electrolytes"),
        default_difficulty="hard",
    ),
    "chronic kidney disease": TopicNode(
        topic="Chronic Kidney Disease",
        category="Nephrology",
        prerequisites=("Renal Physiology", "Hypertension"),
        related_topics=("Hypertension Management", "Acute Kidney Injury"),
        default_difficulty="medium",
    ),
}


def get_topic_node(topic: str) -> TopicNode | None:
    """Retrieve TopicNode by case-insensitive name, or None if topic not indexed."""
    return STATIC_TAXONOMY.get(topic.strip().lower())


def get_prerequisites(topic: str) -> tuple[str, ...]:
    """Return prerequisites for a given topic."""
    node = get_topic_node(topic)
    return node.prerequisites if node else ()


def get_category(topic: str) -> str:
    """Return clinical category/specialty for a given topic."""
    node = get_topic_node(topic)
    return node.category if node else "General Medicine"


def get_related_topics(topic: str) -> tuple[str, ...]:
    """Return related topics in the curriculum graph."""
    node = get_topic_node(topic)
    return node.related_topics if node else ()


def list_all_topics() -> tuple[str, ...]:
    """Return canonical names of all cataloged medical topics."""
    return tuple(node.topic for node in STATIC_TAXONOMY.values())


def get_category_topics(category: str) -> tuple[str, ...]:
    """Return all topics belonging to a clinical category."""
    cat_clean = category.strip().lower()
    return tuple(
        node.topic for node in STATIC_TAXONOMY.values()
        if node.category.lower() == cat_clean
    )

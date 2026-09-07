"""Stage-E: Adaptive Learning & Student Intelligence Layer.
"""

from .models import (
    ConfidenceLevel,
    KnowledgeGap,
    LearningRecommendation,
    LearningReport,
    MasteryLevel,
    QuestionAttempt,
    QuestionDifficulty,
    RecommendationPriority,
    StudentProfile,
    TopicMastery,
)
from .performance_tracker import (
    calculate_accuracy,
    calculate_topic_mastery,
    detect_learning_gaps,
    detect_weak_topics,
    determine_confidence_level,
    determine_mastery_level,
)
from .knowledge_graph import (
    STATIC_TAXONOMY,
    TopicNode,
    get_category,
    get_category_topics,
    get_prerequisites,
    get_related_topics,
    get_topic_node,
    list_all_topics,
)
from .student_profile import (
    calculate_aggregate_learning_level,
    create_initial_profile,
    update_student_profile,
)
from .recommendation import (
    compile_next_learning_actions,
    generate_recommendations,
)
from .pipeline import StageEPipeline

__all__ = [
    # Models
    "ConfidenceLevel",
    "KnowledgeGap",
    "LearningRecommendation",
    "LearningReport",
    "MasteryLevel",
    "QuestionAttempt",
    "QuestionDifficulty",
    "RecommendationPriority",
    "StudentProfile",
    "TopicMastery",
    # Performance
    "calculate_accuracy",
    "calculate_topic_mastery",
    "detect_learning_gaps",
    "detect_weak_topics",
    "determine_confidence_level",
    "determine_mastery_level",
    # Knowledge Graph
    "STATIC_TAXONOMY",
    "TopicNode",
    "get_category",
    "get_category_topics",
    "get_prerequisites",
    "get_related_topics",
    "get_topic_node",
    "list_all_topics",
    # Student Profile
    "calculate_aggregate_learning_level",
    "create_initial_profile",
    "update_student_profile",
    # Recommendations
    "compile_next_learning_actions",
    "generate_recommendations",
    # Pipeline
    "StageEPipeline",
]

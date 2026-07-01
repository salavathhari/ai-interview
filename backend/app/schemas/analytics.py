from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class TopicMetric(BaseModel):
    topic: str
    average_score: float
    question_count: int
    trend: Optional[str] = "stable"


class TrendPoint(BaseModel):
    date: datetime
    score: float


class SkillHeatmapItem(BaseModel):
    skill: str
    category: str
    proficiency: float
    trend: str
    evidence_count: int
    last_assessed: Optional[datetime] = None


class LearningProgressSummary(BaseModel):
    total_hours: float
    completed_topics: int
    in_progress_topics: int
    total_topics: int
    completion_rate: float
    streak_days: int
    daily_hours: List[TrendPoint]
    weekly_hours: List[TrendPoint]


class CodingAnalyticsResponse(BaseModel):
    total_sessions: int
    total_submissions: int
    avg_correctness: float
    avg_runtime_ms: float
    avg_memory_kb: float
    avg_ai_score: float
    language_distribution: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    topic_performance: List[TopicMetric]
    recent_trends: List[TrendPoint]
    improvement_rate: float


class SkillAnalyticsResponse(BaseModel):
    total_skills: int
    skills_learned: int
    skills_mastered: int
    weak_skills: List[SkillHeatmapItem]
    strong_skills: List[SkillHeatmapItem]
    heatmap: List[SkillHeatmapItem]
    improvement_skills: List[SkillHeatmapItem]
    declining_skills: List[SkillHeatmapItem]


class LearningAnalyticsResponse(BaseModel):
    total_hours: float
    completed_topics: int
    in_progress_topics: int
    total_topics: int
    completion_rate: float
    streak_days: int
    daily_hours: List[TrendPoint]
    weekly_hours: List[TrendPoint]
    monthly_hours: List[TrendPoint]
    roadmap_completion: float
    progress_trend: List[TrendPoint]


class CareerAnalyticsResponse(BaseModel):
    overall_readiness: float
    resume_match: float
    ats_score: float
    interview_readiness: float
    coding_readiness: float
    learning_progress: float
    skill_gap_score: float
    role_readiness: Dict[str, float]
    company_readiness: Dict[str, float]
    readiness_trend: List[TrendPoint]
    improvement_rate: float


class TopicAnalyticsResponse(BaseModel):
    topic_scores: List[TopicMetric]
    weak_topics: List[TopicMetric]
    strong_topics: List[TopicMetric]
    topic_trends: Dict[str, List[TrendPoint]]
    improvement_topics: List[TopicMetric]
    declining_topics: List[TopicMetric]


class HistoricalTrendResponse(BaseModel):
    daily: List[TrendPoint]
    weekly: List[TrendPoint]
    monthly: List[TrendPoint]
    career_timeline: List[TrendPoint]
    interview_timeline: List[TrendPoint]
    coding_timeline: List[TrendPoint]
    learning_timeline: List[TrendPoint]


class PredictionResponse(BaseModel):
    predicted_readiness: float
    predicted_interview_success: float
    predicted_coding_success: float
    estimated_time_to_target: str
    learning_completion_forecast: str
    interview_improvement_forecast: str
    confidence: float
    factors: List[str]


class RecommendationResponse(BaseModel):
    next_skill: Optional[str] = None
    next_interview_topic: Optional[str] = None
    next_coding_topic: Optional[str] = None
    next_mini_project: Optional[str] = None
    revision_topics: List[str] = []
    priority_actions: List[Dict[str, str]] = []


class DashboardSummaryResponse(BaseModel):
    average_score: float
    total_interviews: int
    weak_topics: List[TopicMetric]
    strong_topics: List[TopicMetric]
    skill_breakdown: Dict[str, float]


class AnalyticsResponse(BaseModel):
    average_score: float
    total_interviews: int
    weak_topics: List[TopicMetric]
    strong_topics: List[TopicMetric]
    progress_trends: List[TrendPoint]
    role_distribution: Dict[str, int]
    avg_accuracy: float
    avg_communication: float
    avg_confidence: float
    avg_completeness: float
    average_response_speed: float
    hesitation_score: float
    pressure_handling: float
    confidence_estimation: float
    improvement_rate: float
    coding: Optional[CodingAnalyticsResponse] = None
    skills: Optional[SkillAnalyticsResponse] = None
    learning: Optional[LearningAnalyticsResponse] = None
    career: Optional[CareerAnalyticsResponse] = None
    topics: Optional[TopicAnalyticsResponse] = None
    history: Optional[HistoricalTrendResponse] = None
    predictions: Optional[PredictionResponse] = None
    recommendations: Optional[RecommendationResponse] = None

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Question:
    question_no: Optional[int] = None
    question: Optional[str] = None
    model_answer: Optional[str] = None
    candidate_answer: Optional[str] = None
    asked: Optional[bool] = None
    matching_score: Optional[float] = None
    matching_review: Optional[str] = None
    color: Optional[str] = None


@dataclass
class Candidate:
    mongo_id : Optional[str] = None
    candidate_name: Optional[str] = None
    position_applied_for : Optional[str] = None
    resume_summary: Optional[str] = None
    jd_summary: Optional[str] = None
    overview: Optional[str] = None
    final_conclusion :Optional[str] = None
    matching_score: Optional[float] = None
    matched_skills : Optional[str] = None
    non_matched_skills : Optional[str] = None
    expertise_level : Optional[str] = None
    status: Optional[str] = None
    questions: List[Question] = field(default_factory=list)

@dataclass
class Match:
    matching_score : Optional[str] = None
    whats_Wrong : Optional[str] = None
    match_level : Optional[str] = None
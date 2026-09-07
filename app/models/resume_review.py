"""Data models for the five resume review agent outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BrutalReviewResult(BaseModel):
    """Output of the Brutal Honest Review agent.

    Simulates a senior hiring manager's unfiltered first-impression critique.
    """

    overall_assessment: str = ""
    weak_areas: list[str] = Field(default_factory=list)
    missing_elements: list[str] = Field(default_factory=list)
    immediate_rejections: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    actionable_fixes: list[str] = Field(default_factory=list)


class ATSBulletRestructuring(BaseModel):
    """A single bullet-point restructure suggestion for ATS optimisation."""

    original: str
    suggested: str
    reason: str


class ATSOptimizationResult(BaseModel):
    """Output of the ATS Optimizer agent.

    Compares a resume against a specific job description and identifies
    keyword gaps and structural improvements for ATS screening.
    """

    missing_keywords: list[str] = Field(default_factory=list)
    skills_to_highlight: list[str] = Field(default_factory=list)
    bullet_restructurings: list[ATSBulletRestructuring] = Field(
        default_factory=list
    )
    ats_score_estimate: float = 0.0
    summary: str = ""


class BulletTransform(BaseModel):
    """A single bullet-point before-and-after transformation."""

    original: str
    transformed: str
    action_verb: str
    task: str
    result: str


class BulletPointResult(BaseModel):
    """Output of the Bullet Point Transformer agent.

    Rewrites each resume bullet using the Action Verb + Task + Measurable
    Result formula and surfaces questions when quantifiable results are missing.
    """

    original_bullets: list[str] = Field(default_factory=list)
    transformed_bullets: list[BulletTransform] = Field(default_factory=list)
    questions_for_user: list[str] = Field(default_factory=list)


class IndustryToneResult(BaseModel):
    """Output of the Industry Tone Match agent.

    Rewrites the resume summary and skills section to match the tone,
    language, and values of target companies in a given industry.
    """

    original_summary: str = ""
    rewritten_summary: str = ""
    original_skills: list[str] = Field(default_factory=list)
    rewritten_skills: list[str] = Field(default_factory=list)
    tone_analysis: str = ""
    industry_alignment_score: float = 0.0


class TenseIssue(BaseModel):
    """A detected tense inconsistency."""

    section: str
    original: str
    fixed: str


class ClicheReplacement(BaseModel):
    """A cliche phrase and its stronger replacement."""

    original: str
    replacement: str
    reason: str


class GenericToSpecific(BaseModel):
    """A generic phrase improved with specific language."""

    original: str
    improved: str


class FinalPolishResult(BaseModel):
    """Output of the Final Polish agent.

    Audits the entire resume for tense consistency, cliches, and generic
    language, replacing them with specific, powerful alternatives.
    """

    tense_issues: list[TenseIssue] = Field(default_factory=list)
    cliche_replacements: list[ClicheReplacement] = Field(default_factory=list)
    generic_to_specific: list[GenericToSpecific] = Field(default_factory=list)
    overall_quality_score: float = 0.0
    final_summary: str = ""


class FullReviewResult(BaseModel):
    """Combined output of all five review agents."""

    brutal_review: BrutalReviewResult | None = None
    ats_optimization: ATSOptimizationResult | None = None
    bullet_points: BulletPointResult | None = None
    industry_tone: IndustryToneResult | None = None
    final_polish: FinalPolishResult | None = None

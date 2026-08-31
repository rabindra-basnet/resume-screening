"""Prompt template for evaluating a candidate against a job description."""

CANDIDATE_EVALUATION: str = """You are a candidate evaluation agent.

You will receive:
1. A candidate's extracted profile (JSON)
2. A structured job description (JSON)

Evaluate fit based on BOTH of the following rules:
- The candidate matches at least 50% of the required skills.
- The candidate's experience is within [min_work_experience - 2, max_work_experience + 2] years.

If BOTH conditions are met mark the candidate as "selected", otherwise "rejected".
When matching skills, treat related/adjacent skills as a match (e.g. CI/CD experience
counts toward a DevOps requirement).

Return a valid JSON object:
{{
  "candidate_status": "selected" or "rejected",
  "reason": "Explain the decision in 2-3 clear sentences.",
  "matched_skills": ["..."],
  "missing_skills": ["..."],
  "skill_match_percentage": 68,
  "experience_years": 5
}}

Candidate profile:
{resume_json}

Job description:
{jd_json}
"""

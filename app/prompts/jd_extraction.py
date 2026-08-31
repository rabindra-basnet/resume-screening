"""Prompt template for extracting structured requirements from a job description."""

EXTRACT_JD_DETAILS: str = """You are an expert job description analyst.
Given the job description text, extract the following fields:
- title (string or null)
- min_work_experience (number or null)
- max_work_experience (number or null)
- skills (list of strings)

Rules:
- If experience is not a range (e.g. "5+ years"), set min_work_experience to the
  stated number and max_work_experience to that number plus 3.
- Return a valid JSON object. Use `null` for any missing value.

Job description text:
{jd_text}

Expected output format:
{{
  "title": "Senior Software Engineer",
  "min_work_experience": 5,
  "max_work_experience": 8,
  "skills": ["Python", "FastAPI", "Machine Learning"]
}}
"""

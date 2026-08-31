"""Prompt template for extracting a structured candidate profile from a resume."""

EXTRACT_CANDIDATE_DETAILS: str = """You are an expert resume screening assistant.
Extract the following structured fields from the supplied resume text:
- name (string or null)
- email (string or null)
- phone (string or null)
- education (list of objects with degree, institution, field_of_study, or null)
- work_experience_years (number or null, total years of experience)
- skills (list of strings)
- certifications (list of strings)
- work_history (list of objects with company, title, years, or null)

Return a valid JSON object. Use `null` for any missing value.

Resume text:
{resume_text}

Expected output format:
{{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "1234567890",
  "education": [
    {{"degree": "BSc Computer Science", "institution": "Example University",
      "field_of_study": "Computer Science"}}
  ],
  "work_experience_years": 7,
  "skills": ["Python", "FastAPI", "Machine Learning"],
  "certifications": ["Certified Python Developer"],
  "work_history": [
    {{"company": "Example Corp", "title": "Senior Engineer", "years": 3}}
  ]
}}
"""

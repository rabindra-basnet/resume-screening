"""Curated learning resource library keyed by skill.

Provides a deterministic fallback library of high-quality learning resources
for common skills, so a learning plan can be produced without an extra LLM
call for well-known topics. Resources are organized by normalized skill name.
"""

from __future__ import annotations

from app.models.learning import LearningResource

_CURATED: dict[str, list[LearningResource]] = {
    "python": [
        LearningResource(
            skill="Python",
            title="Python for Everybody",
            url="https://www.coursera.org/specializations/python",
            resource_type="course",
            provider="Coursera / University of Michigan",
            description="Comprehensive Python fundamentals from syntax to data structures.",
            estimated_hours=60,
        ),
        LearningResource(
            skill="Python",
            title="Automate the Boring Stuff with Python",
            url="https://automatetheboringstuff.com/",
            resource_type="book",
            provider="Al Sweigart",
            description="Practical Python for real-world automation and scripting.",
            estimated_hours=40,
        ),
    ],
    "fastapi": [
        LearningResource(
            skill="FastAPI",
            title="FastAPI Official Tutorial",
            url="https://fastapi.tiangolo.com/tutorial/",
            resource_type="course",
            provider="FastAPI Docs",
            description="Official comprehensive tutorial covering routes, models, and deps.",
            estimated_hours=20,
        ),
    ],
    "typescript": [
        LearningResource(
            skill="TypeScript",
            title="TypeScript Handbook",
            url="https://www.typescriptlang.org/docs/handbook/intro.html",
            resource_type="book",
            provider="TypeScript",
            description="Official handbook covering the language, types, and advanced features.",
            estimated_hours=25,
        ),
    ],
    "react": [
        LearningResource(
            skill="React",
            title="React Official Tutorial",
            url="https://react.dev/learn",
            resource_type="course",
            provider="React",
            description="Learn React from scratch with interactive examples.",
            estimated_hours=30,
        ),
    ],
    "next.js": [
        LearningResource(
            skill="Next.js",
            title="Next.js Learn",
            url="https://nextjs.org/learn",
            resource_type="course",
            provider="Next.js",
            description="Official interactive course covering the App Router, SSR, and API routes.",
            estimated_hours=25,
        ),
    ],
    "docker": [
        LearningResource(
            skill="Docker",
            title="Docker for Beginners",
            url="https://docker-curriculum.com/",
            resource_type="course",
            provider="docker-curriculum",
            description="Hands-on introduction to containerization with Docker.",
            estimated_hours=10,
        ),
    ],
    "kubernetes": [
        LearningResource(
            skill="Kubernetes",
            title="Kubernetes Basics",
            url="https://kubernetes.io/docs/tutorials/kubernetes-basics/",
            resource_type="course",
            provider="Kubernetes Docs",
            description="Interactive tutorial covering pods, deployments, and services.",
            estimated_hours=15,
        ),
        LearningResource(
            skill="Kubernetes",
            title="Kubernetes the Hard Way",
            url="https://github.com/kelseyhightower/kubernetes-the-hard-way",
            resource_type="practice",
            provider="Kelsey Hightower",
            description="Hands-on walkthrough bootstrapping a Kubernetes cluster from scratch.",
            estimated_hours=30,
        ),
    ],
    "sql": [
        LearningResource(
            skill="SQL",
            title="SQLBolt",
            url="https://sqlbolt.com/",
            resource_type="practice",
            provider="SQLBolt",
            description="Interactive SQL lessons and exercises covering queries through joins.",
            estimated_hours=10,
        ),
        LearningResource(
            skill="SQL",
            title="PostgreSQL Tutorial",
            url="https://www.postgresqltutorial.com/",
            resource_type="course",
            provider="PostgreSQL Tutorial",
            description="Learn PostgreSQL from basics to advanced features.",
            estimated_hours=20,
        ),
    ],
    "aws": [
        LearningResource(
            skill="AWS",
            title="AWS Cloud Practitioner Essentials",
            url="https://aws.amazon.com/training/learn-about/cloud-practitioner/",
            resource_type="course",
            provider="AWS",
            description="Foundation course for core AWS services and the cloud practitioner exam.",
            estimated_hours=15,
        ),
    ],
    "machine learning": [
        LearningResource(
            skill="Machine Learning",
            title="Machine Learning Specialization",
            url="https://www.coursera.org/specializations/machine-learning-introduction",
            resource_type="course",
            provider="Coursera / Stanford",
            description="Foundational ML course covering supervised and unsupervised learning.",
            estimated_hours=60,
        ),
    ],
    "data structures": [
        LearningResource(
            skill="Data Structures",
            title="NeetCode Data Structures",
            url="https://neetcode.io/",
            resource_type="practice",
            provider="NeetCode",
            description="Curated list of data structure and algorithm problems with explanations.",
            estimated_hours=40,
        ),
    ],
    "git": [
        LearningResource(
            skill="Git",
            title="Learn Git Branching",
            url="https://learngitbranching.js.org/",
            resource_type="practice",
            provider="Learn Git Branching",
            description="Interactive visual way to learn git branching and workflows.",
            estimated_hours=5,
        ),
    ],
    "agile": [
        LearningResource(
            skill="Agile",
            title="Agile Fundamentals",
            url="https://www.coursera.org/learn/agile-fundamentals",
            resource_type="course",
            provider="Coursera / University of Virginia",
            description="Learn Scrum and agile practices for product development.",
            estimated_hours=15,
        ),
    ],
    "api": [
        LearningResource(
            skill="API Development",
            title="REST API Best Practices",
            url="https://restfulapi.net/",
            resource_type="article",
            provider="restfulapi.net",
            description="Reference for designing clean, scalable REST APIs.",
            estimated_hours=8,
        ),
    ],
    "pandas": [
        LearningResource(
            skill="Pandas",
            title="Pandas Tutorial",
            url="https://pandas.pydata.org/docs/getting_started/index.html",
            resource_type="course",
            provider="Pandas Docs",
            description="Official getting-started guide for pandas data manipulation.",
            estimated_hours=15,
        ),
    ],
    "testing": [
        LearningResource(
            skill="Testing",
            title="Test-Driven Development with Python",
            url="https://www.obeythetestinggoat.com/",
            resource_type="book",
            provider="Harry Percival",
            description="Hands-on introduction to TDD in Python with Django.",
            estimated_hours=25,
        ),
    ],
    "linux": [
        LearningResource(
            skill="Linux",
            title="Linux Journey",
            url="https://linuxjourney.com/",
            resource_type="course",
            provider="Linux Journey",
            description="Free tutorial covering Linux command line from basics to advanced.",
            estimated_hours=12,
        ),
    ],
    "prompt engineering": [
        LearningResource(
            skill="Prompt Engineering",
            title="Prompt Engineering Guide",
            url="https://www.promptingguide.ai/",
            resource_type="article",
            provider="DAIR.AI",
            description="Comprehensive guide to techniques for effective LLM prompting.",
            estimated_hours=8,
        ),
    ],
    "llm": [
        LearningResource(
            skill="LLM / AI",
            title="Hugging Face NLP Course",
            url="https://huggingface.co/learn/nlp-course",
            resource_type="course",
            provider="Hugging Face",
            description="End-to-end course on transformer models and practical NLP with LLMs.",
            estimated_hours=40,
        ),
    ],
    "javascript": [
        LearningResource(
            skill="JavaScript",
            title="JavaScript.info",
            url="https://javascript.info/",
            resource_type="book",
            provider="javascript.info",
            description="Modern JavaScript tutorial from fundamentals to advanced topics.",
            estimated_hours=50,
        ),
    ],
    "terraform": [
        LearningResource(
            skill="Terraform",
            title="Terraform Beginner's Guide",
            url="https://developer.hashicorp.com/terraform/tutorials/aws-get-started",
            resource_type="course",
            provider="HashiCorp",
            description="Official tutorials covering HCL, state, and provisioning AWS resources.",
            estimated_hours=15,
        ),
    ],
    "ci/cd": [
        LearningResource(
            skill="CI/CD",
            title="GitHub Actions Documentation",
            url="https://docs.github.com/en/actions",
            resource_type="article",
            provider="GitHub",
            description="Complete reference for building CI/CD pipelines with GitHub Actions.",
            estimated_hours=10,
        ),
    ],
}


def curated_resources_for_skill(skill: str) -> list[LearningResource]:
    """Return curated resources for a skill, if any exist.

    Args:
        skill: The skill name to look up.

    Returns:
        A list of matching :class:`LearningResource` objects. May be empty if
        the skill has no curated resources.
    """
    normalized = skill.strip().lower()
    for key, resources in _CURATED.items():
        if key in normalized or normalized in key:
            return list(resources)
    return []


def has_curated_resources(skill: str) -> bool:
    """Return whether any curated resources exist for the given skill.

    Args:
        skill: The skill name to check.

    Returns:
        ``True`` if at least one curated resource matches.
    """
    return bool(curated_resources_for_skill(skill))

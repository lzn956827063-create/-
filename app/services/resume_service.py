from typing import Optional, Dict, Any
from app.db.database import db
from app.db.models import ResumeData


# Default empty resume structure
DEFAULT_RESUME = {
    "basic_info": {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "website": "",
        "title": "",
        "summary": "",
    },
    "skills": [],
    "experience": [],
    "education": [],
    "projects": [],
    "additional": {
        "languages": [],
        "certifications": [],
        "interests": [],
    },
}


class ResumeService:
    """Business logic for the singleton resume row."""

    @staticmethod
    def ensure_default_resume() -> ResumeData:
        """Create the default resume row if it doesn't exist."""
        resume = db.session.get(ResumeData, 1)
        if resume is None:
            resume = ResumeData(
                id=1,
                basic_info=DEFAULT_RESUME["basic_info"],
                skills=DEFAULT_RESUME["skills"],
                experience=DEFAULT_RESUME["experience"],
                education=DEFAULT_RESUME["education"],
                projects=DEFAULT_RESUME["projects"],
                additional=DEFAULT_RESUME["additional"],
            )
            db.session.add(resume)
            db.session.commit()
        return resume

    @staticmethod
    def get_resume() -> Optional[ResumeData]:
        """Get the singleton resume row."""
        return db.session.get(ResumeData, 1)

    @staticmethod
    def get_resume_dict() -> Dict[str, Any]:
        """Get resume as a dict, creating the default if needed."""
        resume = ResumeService.get_resume()
        if resume is None:
            resume = ResumeService.ensure_default_resume()
        return resume.to_dict()

    @staticmethod
    def update_resume(data: Dict[str, Any]) -> ResumeData:
        """Replace the entire resume document."""
        resume = db.session.get(ResumeData, 1)
        if resume is None:
            resume = ResumeData(id=1)
            db.session.add(resume)

        # Update each section if provided
        if "basic_info" in data:
            resume.basic_info = data["basic_info"]
        if "skills" in data:
            resume.skills = data["skills"]
        if "experience" in data:
            resume.experience = data["experience"]
        if "education" in data:
            resume.education = data["education"]
        if "projects" in data:
            resume.projects = data["projects"]
        if "additional" in data:
            resume.additional = data["additional"]

        db.session.commit()
        return resume

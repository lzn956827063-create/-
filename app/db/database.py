from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()


def init_db(app: Flask):
    """Initialize the database with the Flask app and create all tables."""
    db.init_app(app)
    with app.app_context():
        from app.db.models import BlogCategory, BlogPost, BlogComment, ResumeData  # noqa

        db.create_all()

        # Seed default resume row if it doesn't exist
        from app.services.resume_service import ResumeService

        ResumeService.ensure_default_resume()

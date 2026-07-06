from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from app.api import blog_api, resume_api, ai_api  # noqa  — register routes

from flask import Blueprint, render_template

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/edit")
def admin_index():
    """Hidden unified admin dashboard."""
    return render_template("admin/index.html")


@admin_bp.route("/edit/blog")
def blog_editor():
    """Blog CRUD manager page (also handles /edit/blog/new and /edit/blog/<id> via JS)."""
    return render_template("admin/blog_editor.html")


@admin_bp.route("/edit/resume")
def resume_editor():
    """AI-powered resume editor page."""
    return render_template("admin/resume_editor.html")

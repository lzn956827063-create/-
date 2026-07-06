import os
import uuid

from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename

from app.api import api_bp
from app.services.blog_service import BlogService, CategoryHasPostsError
from app.utils.validators import validate_slug, validate_required


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@api_bp.route("/blog/categories", methods=["GET"])
def list_categories():
    cats = BlogService.get_all_categories()
    return jsonify([c.to_dict() for c in cats])


@api_bp.route("/blog/categories", methods=["POST"])
def create_category():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    slug = data.get("slug", "").strip()

    ok, err = validate_required(name, "Category name")
    if not ok:
        return jsonify({"error": err}), 400

    ok, normalized = validate_slug(slug or name)
    if not ok:
        return jsonify({"error": "Invalid slug"}), 400
    slug = normalized

    existing = BlogService.get_category_by_slug(slug)
    if existing:
        return jsonify({"error": f"Category slug '{slug}' already exists"}), 409

    cat = BlogService.create_category(name, slug, data.get("description", ""))
    return jsonify(cat.to_dict()), 201


@api_bp.route("/blog/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    data = request.get_json(silent=True) or {}
    cat = BlogService.update_category(
        category_id,
        name=data.get("name"),
        slug=data.get("slug"),
        description=data.get("description"),
    )
    if not cat:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(cat.to_dict())


@api_bp.route("/blog/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    try:
        BlogService.delete_category(category_id)
        return jsonify({"ok": True})
    except CategoryHasPostsError as e:
        return jsonify({"error": str(e)}), 409
    except Exception:
        return jsonify({"error": "Category not found"}), 404


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------
@api_bp.route("/blog/posts", methods=["GET"])
def list_posts():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    category_id = request.args.get("category_id", type=int)
    search = request.args.get("search")
    published_only = request.args.get("published_only", "1") != "0"

    result = BlogService.get_posts(
        page=page,
        per_page=per_page,
        category_id=category_id,
        search=search,
        published_only=published_only,
    )
    return jsonify(result)


@api_bp.route("/blog/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    post = BlogService.get_post_by_id(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post.to_dict())


@api_bp.route("/blog/posts", methods=["POST"])
def create_post():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    content_md = data.get("content_md", "").strip()
    slug = data.get("slug", "").strip()

    ok, err = validate_required(title, "Title", max_length=200)
    if not ok:
        return jsonify({"error": err}), 400

    ok, normalized = validate_slug(slug or title)
    if not ok:
        return jsonify({"error": "Invalid slug"}), 400
    slug = normalized

    existing = BlogService.get_post_by_slug(slug)
    if existing:
        return jsonify({"error": f"Post slug '{slug}' already exists"}), 409

    post = BlogService.create_post(
        title=title,
        slug=slug,
        content_md=content_md,
        excerpt=data.get("excerpt"),
        cover_image=data.get("cover_image"),
        category_id=data.get("category_id"),
        is_published=data.get("is_published", False),
    )
    return jsonify(post.to_dict()), 201


@api_bp.route("/blog/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    data = request.get_json(silent=True) or {}
    post = BlogService.update_post(
        post_id,
        title=data.get("title"),
        slug=data.get("slug"),
        content_md=data.get("content_md"),
        excerpt=data.get("excerpt"),
        cover_image=data.get("cover_image"),
        category_id=data.get("category_id"),
        is_published=data.get("is_published"),
    )
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post.to_dict())


@api_bp.route("/blog/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    ok = BlogService.delete_post(post_id)
    if not ok:
        return jsonify({"error": "Post not found"}), 404
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------
@api_bp.route("/blog/posts/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    post = BlogService.get_post_by_id(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    comments = BlogService.get_comments(post_id)
    return jsonify([c.to_dict() for c in comments])


@api_bp.route("/blog/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    ok = BlogService.delete_comment(comment_id)
    if not ok:
        return jsonify({"error": "Comment not found"}), 404
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Image upload
# ---------------------------------------------------------------------------
@api_bp.route("/blog/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    if not _allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use: png, jpg, gif, webp"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return jsonify({"url": f"/uploads/{filename}", "filename": filename}), 201

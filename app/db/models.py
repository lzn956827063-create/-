from datetime import datetime, timezone
from app.db.database import db


class BlogCategory(db.Model):
    __tablename__ = "blog_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    posts = db.relationship("BlogPost", back_populates="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "post_count": self.posts.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content_md = db.Column(db.Text, nullable=False, default="")
    content_html = db.Column(db.Text, nullable=False, default="")
    excerpt = db.Column(db.String(500), nullable=True)
    cover_image = db.Column(db.String(500), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("blog_categories.id"), nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    category = db.relationship("BlogCategory", back_populates="posts")
    comments = db.relationship(
        "BlogComment", back_populates="post", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self, include_html=True):
        result = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "content_md": self.content_md,
            "excerpt": self.excerpt,
            "cover_image": self.cover_image,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "category_slug": self.category.slug if self.category else None,
            "is_published": self.is_published,
            "view_count": self.view_count,
            "comment_count": self.comments.count(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_html:
            result["content_html"] = self.content_html
        return result


class BlogComment(db.Model):
    __tablename__ = "blog_comments"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    post = db.relationship("BlogPost", back_populates="comments")

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "author_name": self.author_name,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ResumeData(db.Model):
    """Singleton resume table — only one row (id=1) stores the entire resume as JSON."""

    __tablename__ = "resume_data"

    id = db.Column(db.Integer, primary_key=True)
    basic_info = db.Column(db.JSON, nullable=False, default=dict)
    skills = db.Column(db.JSON, nullable=False, default=list)
    experience = db.Column(db.JSON, nullable=False, default=list)
    education = db.Column(db.JSON, nullable=False, default=list)
    projects = db.Column(db.JSON, nullable=False, default=list)
    additional = db.Column(db.JSON, nullable=False, default=dict)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "basic_info": self.basic_info,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "projects": self.projects,
            "additional": self.additional,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

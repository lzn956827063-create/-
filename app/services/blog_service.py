from typing import Optional, List, Dict, Any
from app.db.database import db
from app.db.models import BlogCategory, BlogPost, BlogComment
from app.utils.markdown_utils import render_markdown, extract_excerpt
from app.utils.xss_utils import sanitize_html


class BlogService:
    """Business logic for blog categories, posts, and comments."""

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------
    @staticmethod
    def get_all_categories() -> List[BlogCategory]:
        return BlogCategory.query.order_by(BlogCategory.name).all()

    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[BlogCategory]:
        return db.session.get(BlogCategory, category_id)

    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[BlogCategory]:
        return BlogCategory.query.filter_by(slug=slug).first()

    @staticmethod
    def create_category(name: str, slug: str, description: str = "") -> BlogCategory:
        cat = BlogCategory(name=name.strip(), slug=slug.strip(), description=description.strip())
        db.session.add(cat)
        db.session.commit()
        return cat

    @staticmethod
    def update_category(category_id: int, **kwargs) -> Optional[BlogCategory]:
        cat = db.session.get(BlogCategory, category_id)
        if not cat:
            return None
        for key, value in kwargs.items():
            if hasattr(cat, key) and value is not None:
                setattr(cat, key, value.strip() if isinstance(value, str) else value)
        db.session.commit()
        return cat

    @staticmethod
    def delete_category(category_id: int) -> bool:
        cat = db.session.get(BlogCategory, category_id)
        if not cat:
            return False
        if cat.posts.count() > 0:
            raise CategoryHasPostsError(
                f"Category '{cat.name}' has {cat.posts.count()} post(s). Reassign or delete them first."
            )
        db.session.delete(cat)
        db.session.commit()
        return True

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------
    @staticmethod
    def get_posts(
        page: int = 1,
        per_page: int = 10,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        published_only: bool = True,
    ) -> Dict[str, Any]:
        query = BlogPost.query
        if published_only:
            query = query.filter_by(is_published=True)
        if category_id:
            query = query.filter_by(category_id=category_id)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    BlogPost.title.ilike(search_term),
                    BlogPost.content_md.ilike(search_term),
                    BlogPost.excerpt.ilike(search_term),
                )
            )
        query = query.order_by(BlogPost.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "posts": [p.to_dict(include_html=False) for p in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": per_page,
        }

    @staticmethod
    def get_post_by_id(post_id: int) -> Optional[BlogPost]:
        return db.session.get(BlogPost, post_id)

    @staticmethod
    def get_post_by_slug(slug: str) -> Optional[BlogPost]:
        return BlogPost.query.filter_by(slug=slug).first()

    @staticmethod
    def create_post(**kwargs) -> BlogPost:
        post = BlogPost()
        for key, value in kwargs.items():
            if hasattr(post, key) and value is not None:
                setattr(post, key, value.strip() if isinstance(value, str) else value)
        # Render Markdown to HTML and cache it
        if post.content_md:
            post.content_html = render_markdown(post.content_md)
        else:
            post.content_html = ""
        # Auto-generate excerpt if not provided
        if not post.excerpt and post.content_md:
            post.excerpt = extract_excerpt(post.content_md, post.content_html)
        db.session.add(post)
        db.session.commit()
        return post

    @staticmethod
    def update_post(post_id: int, **kwargs) -> Optional[BlogPost]:
        post = db.session.get(BlogPost, post_id)
        if not post:
            return None
        for key, value in kwargs.items():
            if hasattr(post, key) and value is not None:
                setattr(post, key, value.strip() if isinstance(value, str) else value)
        # Re-render Markdown if content changed
        if "content_md" in kwargs:
            post.content_html = render_markdown(post.content_md)
            if not kwargs.get("excerpt"):
                post.excerpt = extract_excerpt(post.content_md, post.content_html)
        db.session.commit()
        return post

    @staticmethod
    def delete_post(post_id: int) -> bool:
        post = db.session.get(BlogPost, post_id)
        if not post:
            return False
        db.session.delete(post)
        db.session.commit()
        return True

    @staticmethod
    def increment_view(post_id: int) -> None:
        post = db.session.get(BlogPost, post_id)
        if post:
            post.view_count = (post.view_count or 0) + 1
            db.session.commit()

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------
    @staticmethod
    def get_comments(post_id: int) -> List[BlogComment]:
        return (
            BlogComment.query.filter_by(post_id=post_id)
            .order_by(BlogComment.created_at.desc())
            .all()
        )

    @staticmethod
    def add_comment(post_id: int, author_name: str, content: str) -> BlogComment:
        comment = BlogComment(
            post_id=post_id,
            author_name=sanitize_html(author_name.strip()),
            content=sanitize_html(content.strip()),
        )
        db.session.add(comment)
        db.session.commit()
        return comment

    @staticmethod
    def delete_comment(comment_id: int) -> bool:
        comment = db.session.get(BlogComment, comment_id)
        if not comment:
            return False
        db.session.delete(comment)
        db.session.commit()
        return True


class CategoryHasPostsError(Exception):
    """Raised when trying to delete a category that still has posts."""
    pass

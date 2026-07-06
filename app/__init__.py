from flask import Flask, render_template
from config import Config


def create_app(config_class=Config):
    """Application factory: creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure data and upload directories exist
    import os

    os.makedirs(app.config["DATABASE_PATH"].rsplit(os.sep, 1)[0], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize database
    from app.db.database import init_db

    init_db(app)

    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.admin_routes import admin_bp
    from app.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app

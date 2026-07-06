from flask import request, jsonify, current_app
from app.api import api_bp
from app.services.ai_service import get_ai_service, AIProviderError

VALID_ACTIONS = {"polish", "tailor", "expand", "proofread"}


@api_bp.route("/ai/optimize", methods=["POST"])
def optimize_text():
    """Optimize a text snippet using the configured AI provider."""
    data = request.get_json(silent=True) or {}

    text = (data.get("text") or "").strip()
    action = (data.get("action") or "polish").strip()
    context = (data.get("context") or "").strip()

    # Validate
    if not text:
        return jsonify({"error": "text is required"}), 400
    if action not in VALID_ACTIONS:
        return jsonify({"error": f"Invalid action. Must be one of: {', '.join(sorted(VALID_ACTIONS))}"}), 400
    if len(text) > 5000:
        return jsonify({"error": "Text must be 5000 characters or fewer"}), 400

    try:
        ai = get_ai_service()
        # Ensure the service is initialized with the app
        ai.init_app(current_app)
        optimized = ai.optimize_text(text, action, context)
        return jsonify({"optimized_text": optimized, "action": action})
    except AIProviderError as e:
        current_app.logger.error(f"AI optimize failed: {e}")
        return jsonify({
            "error": str(e),
            "fallback_text": text,
        }), 503
    except Exception as e:
        current_app.logger.error(f"Unexpected AI error: {e}")
        return jsonify({
            "error": "AI service error",
            "fallback_text": text,
        }), 500

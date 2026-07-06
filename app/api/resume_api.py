from flask import request, jsonify, render_template_string
from app.api import api_bp
from app.services.resume_service import ResumeService

# ---------------------------------------------------------------------------
# Resume template HTML snippets for preview rendering
# ---------------------------------------------------------------------------
RESUME_TEMPLATES = {
    "professional": """
<div class="resume-template resume-professional">
    {% if basic_info.name %}
    <header class="resume-header">
        <h1 class="resume-name">{{ basic_info.name }}</h1>
        <p class="resume-title">{{ basic_info.title }}</p>
        <div class="resume-contact">
            {% if basic_info.email %}<span>{{ basic_info.email }}</span>{% endif %}
            {% if basic_info.phone %}<span>{{ basic_info.phone }}</span>{% endif %}
            {% if basic_info.location %}<span>{{ basic_info.location }}</span>{% endif %}
            {% if basic_info.website %}<span>{{ basic_info.website }}</span>{% endif %}
        </div>
    </header>
    {% endif %}

    {% if basic_info.summary %}
    <section class="resume-section">
        <h2>Professional Summary</h2>
        <p>{{ basic_info.summary }}</p>
    </section>
    {% endif %}

    {% if skills %}
    <section class="resume-section">
        <h2>Skills</h2>
        {% for group in skills %}
        <div class="skill-group">
            <h3>{{ group.category }}</h3>
            <div class="skill-items">
                {% for item in group.items %}
                <span class="skill-tag">{{ item.name }}{% if item.level %} · {{ item.level }}/5{% endif %}</span>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if experience %}
    <section class="resume-section">
        <h2>Experience</h2>
        {% for exp in experience %}
        <div class="resume-entry">
            <div class="entry-header">
                <h3>{{ exp.title }}</h3>
                <span class="entry-org">{{ exp.company }}</span>
                <span class="entry-dates">{{ exp.start }} – {{ exp.end or 'Present' }}</span>
            </div>
            <p>{{ exp.description }}</p>
            {% if exp.highlights %}
            <ul>
                {% for h in exp.highlights %}<li>{{ h }}</li>{% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if education %}
    <section class="resume-section">
        <h2>Education</h2>
        {% for edu in education %}
        <div class="resume-entry">
            <h3>{{ edu.degree }} in {{ edu.field }}</h3>
            <span class="entry-org">{{ edu.school }}</span>
            <span class="entry-dates">{{ edu.start }} – {{ edu.end }}</span>
        </div>
        {% endfor %}
    </section>
    {% endif %}

    {% if projects %}
    <section class="resume-section">
        <h2>Projects</h2>
        {% for proj in projects %}
        <div class="resume-entry">
            <h3>{{ proj.name }}</h3>
            {% if proj.tech %}<span class="entry-tech">{{ proj.tech }}</span>{% endif %}
            <p>{{ proj.description }}</p>
            {% if proj.highlights %}
            <ul>
                {% for h in proj.highlights %}<li>{{ h }}</li>{% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
    </section>
    {% endif %}
</div>
""",
    "modern": """
<div class="resume-template resume-modern">
    <div class="resume-sidebar">
        {% if basic_info.name %}
        <div class="sidebar-header">
            <h1>{{ basic_info.name }}</h1>
            <p class="sidebar-title">{{ basic_info.title }}</p>
        </div>
        {% endif %}

        <div class="sidebar-contact">
            <h3>Contact</h3>
            {% if basic_info.email %}<p>{{ basic_info.email }}</p>{% endif %}
            {% if basic_info.phone %}<p>{{ basic_info.phone }}</p>{% endif %}
            {% if basic_info.location %}<p>{{ basic_info.location }}</p>{% endif %}
            {% if basic_info.website %}<p>{{ basic_info.website }}</p>{% endif %}
        </div>

        {% if skills %}
        <div class="sidebar-skills">
            <h3>Skills</h3>
            {% for group in skills %}
            <h4>{{ group.category }}</h4>
            <ul>
                {% for item in group.items %}
                <li>{{ item.name }}{% if item.level %} ({{ item.level }}/5){% endif %}</li>
                {% endfor %}
            </ul>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <div class="resume-main">
        {% if basic_info.summary %}
        <section><h2>About</h2><p>{{ basic_info.summary }}</p></section>
        {% endif %}
        {% if experience %}
        <section><h2>Experience</h2>
        {% for exp in experience %}
        <div class="entry">
            <h3>{{ exp.title }} · {{ exp.company }}</h3>
            <span class="dates">{{ exp.start }} – {{ exp.end or 'Present' }}</span>
            <p>{{ exp.description }}</p>
        </div>
        {% endfor %}
        </section>
        {% endif %}
        {% if education %}
        <section><h2>Education</h2>
        {% for edu in education %}
        <div class="entry">
            <h3>{{ edu.degree }} · {{ edu.school }}</h3>
            <span class="dates">{{ edu.start }} – {{ edu.end }}</span>
        </div>
        {% endfor %}
        </section>
        {% endif %}
        {% if projects %}
        <section><h2>Projects</h2>
        {% for proj in projects %}
        <div class="entry">
            <h3>{{ proj.name }}</h3>
            <p>{{ proj.description }}</p>
        </div>
        {% endfor %}
        </section>
        {% endif %}
    </div>
</div>
""",
    "minimal": """
<div class="resume-template resume-minimal">
    {% if basic_info.name %}
    <header>
        <h1>{{ basic_info.name }}</h1>
        <p class="headline">{{ basic_info.title }}{% if basic_info.location %} · {{ basic_info.location }}{% endif %}</p>
        <p class="contact-line">
            {% if basic_info.email %}{{ basic_info.email }}{% endif %}
            {% if basic_info.phone %} · {{ basic_info.phone }}{% endif %}
            {% if basic_info.website %} · {{ basic_info.website }}{% endif %}
        </p>
    </header>
    {% endif %}

    {% if basic_info.summary %}
    <section><p class="summary">{{ basic_info.summary }}</p></section>
    {% endif %}

    {% if experience %}
    <section><h2>Experience</h2>
    {% for exp in experience %}
    <div class="entry">
        <strong>{{ exp.title }}</strong> — {{ exp.company }} <em>({{ exp.start }} – {{ exp.end or 'Present' }})</em>
        <p>{{ exp.description }}</p>
    </div>
    {% endfor %}
    </section>
    {% endif %}

    {% if education %}
    <section><h2>Education</h2>
    {% for edu in education %}
    <p><strong>{{ edu.degree }}, {{ edu.field }}</strong> — {{ edu.school }} ({{ edu.start }} – {{ edu.end }})</p>
    {% endfor %}
    </section>
    {% endif %}

    {% if skills %}
    <section><h2>Skills</h2>
    {% for group in skills %}
    <p><strong>{{ group.category }}:</strong> {{ group.items | map(attribute='name') | join(', ') }}</p>
    {% endfor %}
    </section>
    {% endif %}

    {% if projects %}
    <section><h2>Projects</h2>
    {% for proj in projects %}
    <p><strong>{{ proj.name }}</strong> — {{ proj.description }}</p>
    {% endfor %}
    </section>
    {% endif %}
</div>
""",
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@api_bp.route("/resume", methods=["GET"])
def get_resume():
    data = ResumeService.get_resume_dict()
    return jsonify(data)


@api_bp.route("/resume", methods=["PUT"])
def update_resume():
    data = request.get_json(silent=True) or {}
    resume = ResumeService.update_resume(data)
    return jsonify(resume.to_dict())


@api_bp.route("/resume/preview/<template>", methods=["POST"])
def preview_resume(template):
    """Render resume data with a specific template, returning HTML."""
    if template not in RESUME_TEMPLATES:
        return jsonify({"error": f"Unknown template '{template}'. Available: {list(RESUME_TEMPLATES.keys())}"}), 400

    data = request.get_json(silent=True) or {}
    # Merge with stored data: use provided fields, fall back to DB
    stored = ResumeService.get_resume_dict()
    merged = {
        "basic_info": data.get("basic_info", stored.get("basic_info", {})),
        "skills": data.get("skills", stored.get("skills", [])),
        "experience": data.get("experience", stored.get("experience", [])),
        "education": data.get("education", stored.get("education", [])),
        "projects": data.get("projects", stored.get("projects", [])),
        "additional": data.get("additional", stored.get("additional", {})),
    }

    template_str = RESUME_TEMPLATES[template]
    html = render_template_string(template_str, **merged)
    return html

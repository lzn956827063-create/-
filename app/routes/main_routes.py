from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.services.blog_service import BlogService
from app.utils.validators import validate_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def homepage():
    """Portfolio homepage."""
    return render_template("index.html")


@main_bp.route("/blog")
def blog_list():
    """Public blog listing with optional search and category filter."""
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category")
    search = request.args.get("search", "").strip()

    category_id = None
    if category_slug:
        cat = BlogService.get_category_by_slug(category_slug)
        if cat:
            category_id = cat.id

    result = BlogService.get_posts(
        page=page,
        per_page=9,
        category_id=category_id,
        search=search if search else None,
        published_only=True,
    )
    categories = BlogService.get_all_categories()

    return render_template(
        "blog/list.html",
        posts=result["posts"],
        pagination=result,
        categories=categories,
        current_category=category_slug,
        current_search=search,
    )


@main_bp.route("/blog/category/<slug>")
def blog_by_category(slug):
    """Redirect to blog list filtered by category."""
    cat = BlogService.get_category_by_slug(slug)
    if not cat:
        return render_template("errors/404.html"), 404
    return redirect(url_for("main.blog_list", category=slug))


@main_bp.route("/blog/<slug>")
def blog_detail(slug):
    """Single blog post with comments."""
    post = BlogService.get_post_by_slug(slug)
    if not post or not post.is_published:
        return render_template("errors/404.html"), 404

    BlogService.increment_view(post.id)
    comments = BlogService.get_comments(post.id)

    return render_template(
        "blog/detail.html",
        post=post.to_dict(),
        comments=[c.to_dict() for c in comments],
    )


@main_bp.route("/blog/<slug>/comment", methods=["POST"])
def blog_add_comment(slug):
    """Add a comment to a blog post."""
    post = BlogService.get_post_by_slug(slug)
    if not post or not post.is_published:
        return render_template("errors/404.html"), 404

    author_name = request.form.get("author_name", "").strip()
    content = request.form.get("content", "").strip()

    ok, err = validate_required(author_name, "Name", max_length=100)
    if not ok:
        flash(err, "error")
        return redirect(url_for("main.blog_detail", slug=slug))

    ok, err = validate_required(content, "Comment", max_length=2000)
    if not ok:
        flash(err, "error")
        return redirect(url_for("main.blog_detail", slug=slug))

    BlogService.add_comment(post.id, author_name, content)
    flash("评论发布成功！", "success")
    return redirect(url_for("main.blog_detail", slug=slug))


# ======================================================================
# Project demo pages
# ======================================================================

@main_bp.route("/projects/ai-chat")
def project_ai_chat():
    """AI 聊天平台 — 调用阿里云百炼 API 进行对话。"""
    return render_template("projects/ai_chat.html")


@main_bp.route("/projects/dataviz")
def project_dataviz():
    """数据可视化看板 — ECharts 实时交互图表。"""
    return render_template("projects/dataviz.html")


@main_bp.route("/projects/devops")
def project_devops():
    """DevOps 工具箱 — JSON 格式化、时间戳转换、Base64 编解码等。"""
    return render_template("projects/devops.html")


@main_bp.route("/projects/navihub")
def project_navihub():
    """个人导航页 — 极客风起始页，书签、搜索、天气、时钟。"""
    return render_template("projects/navihub.html")


@main_bp.route("/projects/resume-builder")
def project_resume_builder():
    """Markdown 简历生成器 — 在线编辑、实时预览、多模板、导出 PDF。"""
    return render_template("projects/resume_builder.html")


@main_bp.route("/projects/network-monitor")
def project_network_monitor():
    """毕设项目：内网监控面板 — SNMP、延迟、CPU、内存实时监控。"""
    return render_template("projects/network_monitor.html")


@main_bp.route("/projects/dataviz-dashboard")
def project_dataviz_dashboard():
    """DataViz 低代码看板平台 — Schema 驱动、拖拽搭建、版本回滚。"""
    return render_template("projects/dataviz_dashboard.html")


# ======================================================================
# AI Chat API (streaming chat for the AI chat page)
# ======================================================================

@main_bp.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    """AI 聊天接口：接收对话消息，返回 AI 回复。"""
    from app.services.ai_service import get_ai_service, AIProviderError

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return {"error": "请输入消息"}, 400
    if len(message) > 5000:
        return {"error": "消息过长，请控制在 5000 字以内"}, 400

    # 构建对话 messages
    messages = [{"role": "system", "content": "你是一个有帮助的AI助手，用中文回答问题，简洁专业。"}]
    for h in history[-10:]:  # 最多保留 10 轮历史
        if h.get("role") in ("user", "assistant"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    try:
        ai = get_ai_service()
        ai.init_app(current_app)

        # 直接用 provider 的聊天能力
        if hasattr(ai._provider, 'chat'):
            reply = ai._provider.chat(messages)
        else:
            # 回退：用 optimize 模拟聊天
            reply = ai._provider.optimize(message, "polish")
            if not reply or reply == message:
                reply = f"收到你的消息：「{message}」\n\n当前 AI 配置为优化模式，如需对话功能请使用支持 Chat Completion 的模型。"

        return {"reply": reply}
    except AIProviderError as e:
        return {"error": f"AI 服务不可用: {e}", "fallback": f"抱歉，AI 服务暂时不可用。"}, 503
    except Exception as e:
        current_app.logger.error(f"AI chat error: {e}")
        return {"error": "AI 服务异常"}, 500


# ======================================================================
# AI File Analysis API
# ======================================================================

ALLOWED_FILE_EXTENSIONS = {
    "txt", "md", "py", "js", "ts", "html", "css", "json", "xml", "yaml", "yml",
    "csv", "log", "java", "go", "rs", "c", "cpp", "h", "sh", "bat",
    "pdf", "docx", "doc",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@main_bp.route("/api/ai/analyze-file", methods=["POST"])
def ai_analyze_file():
    """上传文件让 AI 分析：提取内容，调用 AI 返回分析结果。"""
    from app.services.ai_service import get_ai_service, AIProviderError

    if "file" not in request.files:
        return {"error": "请选择要上传的文件"}, 400

    file = request.files["file"]
    if not file.filename:
        return {"error": "文件名为空"}, 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_FILE_EXTENSIONS:
        return {"error": f"不支持的文件类型: .{ext}。支持: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"}, 400

    # 检查文件大小
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return {"error": f"文件过大（{size/1024/1024:.1f}MB），最大支持 5MB"}, 400

    # 读取文件内容
    try:
        if ext == "pdf":
            text = _extract_pdf_text(file)
        elif ext in ("docx", "doc"):
            text = _extract_docx_text(file)
        else:
            raw = file.read()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = raw.decode("gbk")
                except UnicodeDecodeError:
                    text = raw.decode("latin-1")
    except Exception as e:
        return {"error": f"文件读取失败: {e}"}, 400

    if not text or not text.strip():
        return {"error": "文件内容为空或无法解析"}, 400

    # 限制文本长度
    if len(text) > 10000:
        text = text[:10000] + "\n\n[文件过长，仅分析前10000字符...]"

    filename = file.filename
    instruction = (request.form.get("instruction") or "分析").strip()
    instruction_map = {
        "分析": "请详细分析以下文件内容，说明其用途、结构和关键信息：",
        "简历优化": "你是一位专业的简历顾问。以下是一份简历文件的内容，请给出详细的优化建议，包括措辞改进、结构优化、亮点提炼等方面：",
        "代码审查": "你是一位资深代码审查专家。请审查以下代码，指出潜在问题、改进建议和最佳实践：",
        "总结": "请用简洁的语言总结以下文件的核心内容：",
        "翻译": "请将以下内容翻译成中文（如果是中文则翻译成英文）：",
    }

    prompt = instruction_map.get(instruction, f"请{instruction}以下文件内容：")
    full_prompt = f"{prompt}\n\n文件名：{filename}\n\n文件内容：\n```\n{text}\n```"

    try:
        ai = get_ai_service()
        ai.init_app(current_app)

        messages = [
            {"role": "system", "content": "你是一个专业的文件分析助手，用中文回答，简洁专业，结构清晰。分析结果使用 Markdown 格式呈现。"},
            {"role": "user", "content": full_prompt},
        ]

        if hasattr(ai._provider, 'chat'):
            reply = ai._provider.chat(messages)
        else:
            reply = ai._provider.optimize(full_prompt, "polish")

        return {"reply": reply, "filename": filename, "instruction": instruction}
    except AIProviderError as e:
        return {"error": f"AI 服务不可用: {e}"}, 503
    except Exception as e:
        current_app.logger.error(f"File analysis error: {e}")
        return {"error": "文件分析服务异常"}, 500


def _extract_pdf_text(file) -> str:
    """从 PDF 文件提取文本。"""
    try:
        import io
        from PyPDF2 import PdfReader

        reader = PdfReader(io.BytesIO(file.read()))
        texts = []
        for page in reader.pages[:10]:  # 最多 10 页
            t = page.extract_text()
            if t:
                texts.append(t)
        return "\n\n".join(texts)
    except ImportError:
        return "PDF 解析需要安装 PyPDF2 库：pip install PyPDF2"


def _extract_docx_text(file) -> str:
    """从 Word 文件提取文本。"""
    try:
        import io
        from docx import Document

        doc = Document(io.BytesIO(file.read()))
        texts = []
        for para in doc.paragraphs[:200]:  # 最多 200 段
            if para.text.strip():
                texts.append(para.text)
        return "\n".join(texts)
    except ImportError:
        return "Word 解析需要安装 python-docx 库：pip install python-docx"

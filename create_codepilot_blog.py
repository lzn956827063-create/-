"""Create blog post for CodePilot AI Agent project."""
from app import create_app
from app.services.blog_service import BlogService
from app.utils.markdown_utils import render_markdown, extract_excerpt

app = create_app()
ctx = app.app_context()
ctx.push()

CODEPILOT_BLOG_MD = """## 为什么要做 CodePilot？

面试的时候，面试官经常会问："你简历上这个项目，具体是怎么实现的？" 如果只是口头描述，很难把架构讲清楚。但如果我有一个工具，能让面试官**直接看到 AI Agent 的思考过程**——每次调用什么工具、读到什么代码、最后怎么得出结论——这比任何技术文档都更有说服力。

这就是 CodePilot 的出发点：一个**面向应届生简历展示**的 AI Agent 项目。

---

## 什么是 AI Agent？和普通聊天 AI 有什么不同？

这是面试中最常被问到的问题。普通人用 ChatGPT 是"你问我答"——一次性给出问题，AI 一次性回答。但 AI Agent 不一样：

| | 普通 AI 聊天 | AI Agent |
|---|---|---|
| 交互方式 | 一问一答 | 自主探索 |
| 获取信息 | 仅靠训练数据 | 调用工具查资料 |
| 决策能力 | 无 | 判断何时需要更多信息 |
| 透明度 | 黑盒 | 每一步可观测 |

在 CodePilot 里，用户问"这个项目的登录功能怎么实现的"，Agent 不会直接猜，而是：

1. 先调用 `get_project_overview` 看项目长什么样
2. 调用 `search_code("login")` 搜相关代码
3. 调用 `read_file("auth/routes.py")` 确认细节
4. 信息够了，给出答案

整个过程，**前端实时展示 Agent 的每一步决策**。这就是 AI Agent 的"可解释性"。

---

## ReAct 架构：AI 如何"思考"？

CodePilot 的 Agent 基于 ReAct（Reasoning + Acting）模式：

```
Thought → Action → Observation → Thought → Action → ... → Final Answer
  思考      执行      观察         再思考     继续     最终答案
```

核心代码在 `agent/agent_loop.py`，一个 `AgentLoop` 类包含完整的 ReAct 循环：

- **Thought**：AI 根据当前信息判断是否需要更多数据
- **Action**：如果需要，从 5 个工具中选择最合适的一个并调用
- **Observation**：拿到工具返回的结果，更新"知识"
- **循环**：最多 8 轮，达到上限自动总结
- **Final Answer**：结构化三段式回答（📌 结论 / 🔍 关键发现 / 💡 补充说明）

这套架构的精妙之处在于**非写死流程**。AI 自己决定每一步用什么工具——它不是按照硬编码的 if-else 执行，而是根据实时反馈动态调整策略。

---

## 三个 Agent，各司其职

CodePilot 实现了 3 个专业 Agent，共用同一套 5 个工具（`tools.py`），但各自的工作方式不同：

### 1. 问答 Agent（AgentLoop）

最灵活、最通用。单阶段循环，用户问什么都可以。每轮对话独立运行，不持久化中间结果。适合"随问随答"的场景。

### 2. 分析 Agent（AnalysisAgent）

两阶段模式：Phase 1（探索）自由调用工具收集源码信息，Phase 2（生成）基于探索摘要产出结构化 JSON 报告。结果持久化到数据库，可反复查看。

### 3. README Agent（ReadmeAgent）

同样是两阶段模式，但关注点偏向"可复现"——安装命令、运行方式、配置方法。输出是纯 Markdown，供下载。

有意思的是，分析和 README 两个 Agent 其实是同一个模式（探索→生成），只是 Prompt 不同。后续如果要加更多 Agent（比如安全审计、测试生成），可以抽一个 `ExploreGenerateAgent` 基类。

---

## Function Calling：零框架依赖

这也是面试加分点。很多 AI Agent 项目依赖 LangChain 等重框架，而 CodePilot **直接使用 DeepSeek 原生 Function Calling API**（兼容 OpenAI 格式），零额外依赖。

工具定义遵循标准的 OpenAI Function Calling JSON Schema：

```json
{
  "name": "search_code",
  "description": "在项目源码中搜索包含指定关键词的文件",
  "parameters": {
    "keyword": { "type": "string", "description": "搜索关键词" },
    "file_pattern": { "type": "string", "description": "可选文件扩展名过滤" }
  }
}
```

这意味着：没有学习新框架的成本、不引入脆弱的依赖链、完全掌控 Agent 的行为逻辑。面试时可以讲清楚每一行代码在做什么。

---

## 技术选型的"为什么"

| 选择 | 原因 |
|---|---|
| FastAPI 而非 Flask | 原生异步支持（Agent 循环中多次 API 调用不能阻塞）|
| SQLite + aiosqlite | 异步 SQLite 驱动，项目和面试环境免安装 |
| Vue 3 + Element Plus | 前端实时展示 Agent 工具调用需要响应式渲染 |
| httpx 而非 requests | 异步 HTTP 客户端，和 FastAPI 的异步模型匹配 |
| DeepSeek 而非 OpenAI | 成本低（1/10 价格），中文代码理解同样优秀 |

---

## 安全机制

Agent 要自动读取文件，安全性是必须考虑的。CodePilot 做了三层防护：

1. **路径穿越防护**：`_tool_read_file` 中 `normpath + startswith` 双重验证，所有文件操作限制在项目目录内
2. **文件过滤**：跳过二进制、图片、字体等不可读文件类型
3. **大小限制**：超过 2MB 的文件不读取，防止内存溢出

---

## 写在最后

CodePilot 是我简历上最满意的项目之一。它不只是"调了一个 API"，而是一个完整的 Agent 系统设计：

- 从零实现了 ReAct 循环（可以讲清楚每一行代码）
- 3 个 Agent 共享工具层，各自定制探索策略
- Function Calling 零框架依赖
- 前端实时展示 AI 决策过程（面试 Demo 效果极佳）
- 完整的异步全链路 + 安全机制

如果你也是应届生，我的建议是：**简历上的项目不要追求数量，而是追求"你能讲多久"**。CodePilot 这个项目我可以从架构讲到 ReAct 循环讲到 Function Calling 讲到一个小时——因为它每一层都是自己写的，没有一处是"别人封装好的"。

源码：[GitHub - CodePilot](https://github.com/lzn956827063-create/CodePilot)
"""

CODEPILOT_HTML = render_markdown(CODEPILOT_BLOG_MD)
CODEPILOT_EXCERPT = extract_excerpt(CODEPILOT_BLOG_MD, CODEPILOT_HTML, 400)

post = BlogService.create_post(
    title="CodePilot：从零构建 AI Agent 代码仓库分析助手（ReAct + Function Calling）",
    slug="codepilot-building",
    content_md=CODEPILOT_BLOG_MD,
    content_html=CODEPILOT_HTML,
    excerpt=CODEPILOT_EXCERPT,
    category_id=1,
    is_published=True,
)
print(f"CodePilot blog: id={post.id}, slug={post.slug}")

ctx.pop()
print("\n=== DONE ===")

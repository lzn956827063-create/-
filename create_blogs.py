"""Create blog posts for Moon Phase Journal and Network Monitor projects."""
from app import create_app
from app.services.blog_service import BlogService
from app.utils.markdown_utils import render_markdown, extract_excerpt

app = create_app()
ctx = app.app_context()
ctx.push()

# ── Blog 1: Moon Phase Journal ──────────────────────
MOON_BLOG_MD = """## 从一个"不美"的赛道切入

经期追踪是一个"老土"的需求——市面上有一大堆同类产品，但它们要么界面像医疗软件，要么充斥着社区、电商和广告。我想做的是一款**更安静**的工具：打开就是一轮月亮，看一眼就知道今天的状态，其他什么都不需要。

这就是月相日记的起点。

---

## 月相作为隐喻

设计上最大的决定是用**月相盈亏映射生理周期**。这不是硬凑概念——女性的月经周期和月相周期都是约 28 天，古希腊医学和中医学都有"天人相应"的论述。

| 阶段 | 月相 | 视觉表达 |
|---|---|---|
| 经期 Day 1-5 | 新月（晦） | 暗色背景 + 细弯月 |
| 卵泡期 Day 6-13 | 渐盈 | 月牙逐渐饱满 |
| 排卵期 Day 14 | 满月（望） | 完整明亮圆月 |
| 黄体期 Day 15-28 | 渐亏 | 月光缓慢消退 |

Canvas 月相绘制是在 Canvas 2D API 上从零写的，没用任何现成的图标库。核心思路是画两个半圆做减法——一个白色圆加一个偏移的暗色遮罩圆，通过调整遮罩圆的 x 偏移来控制月相角度。

---

## 预测算法：从简单平均到自适应

算法设计是另一个我花了心思的地方。需求很明确：根据用户历史记录，预测下一次经期开始日期。

### V1: 简单平均

最直观的做法——取所有历史周期长度的平均值。问题是：一两个异常值（比如熬夜导致的延迟）会让预测偏离很远。

### V2: 异常值过滤 + SMA

升级方案：先过滤掉异常周期（< 60% 或 > 140% 中位数），再对最近的 2-6 个周期做简单移动平均。对于有 3 条以上记录的用户，预测准确度显著提升。

### V3: 趋势修正

有时用户的周期在"变长"或"变短"——比如从 30 天逐渐变成 28 天。简单移动平均无法感知趋势。我做了一层加权移动平均（WMA），给最近周期更高的权重，用 WMA - SMA 的差值作为趋势修正量（限幅 ±2 天）。

```
confidence = 0.15 + min(cycleCount, 7) * 0.14  // cap at 1.0
```

置信度随数据量线性增长：3 条 → 0.3, 6 条 → 0.825, 7+ → 1.0。

---

## 隐私优先

生理周期数据是高度敏感的。我做了几个决策：

1. **全本地存储**：所有数据都在微信 Storage 里，不上传任何服务器
2. **生物识别锁**：从后台切回前台时自动触发指纹/面部验证（基于 WeChat Soter API）
3. **无账号体系**：不需要注册登录，数据跟着手机走

---

## 原生开发的克制

项目完全使用微信原生框架（WXML + WXSS + JS + Canvas），没有引入任何第三方 UI 库。好处是：包体积极小、启动快、不依赖外部更新；代价是：所有交互细节都要自己写——日历组件的滑动切换、弹出层的动画、Canvas 的像素级绘制。

这实际上是一个挺好的练习——在框架提供的最基础能力上，把用户体验做到位。

---

## 目前状态

项目核心功能已完成（周期追踪、预测、日历、月相动画、隐私保护），仍在迭代中。计划后续提交微信审核上架。

源码：[GitHub - moon-phase-journal](https://github.com/lzn956827063-create/moon-phase-journal)
"""

MOON_HTML = render_markdown(MOON_BLOG_MD)
MOON_EXCERPT = extract_excerpt(MOON_BLOG_MD, MOON_HTML, 400)

post = BlogService.create_post(
    title="月相日记：用月相隐喻女性身体节律的微信小程序",
    slug="moon-phase-journal-building",
    content_md=MOON_BLOG_MD,
    content_html=MOON_HTML,
    excerpt=MOON_EXCERPT,
    category_id=1,
    is_published=True,
)
print(f"Moon Phase blog: id={post.id}, slug={post.slug}")

# ── Blog 2: Network Monitor ─────────────────────────
NETWORK_BLOG_MD = """## 毕设选题：为什么选网络监控？

2026 届毕业设计，我选了"企业内网实时监控系统"这个题目。出发点很实际：中小企业的 IT 运维大多依赖人工巡检——出了问题才发现，而不是提前感知。而市面上的监控方案（Zabbix、Prometheus + Grafana）对企业 IT 人员来说门槛偏高。

我的目标是做一个**轻量、易部署、开箱即用**的内网监控面板。

---

## 技术选型

| 层次 | 技术 | 原因 |
|---|---|---|
| 后端框架 | Flask 3.x | 轻量、Python 生态、快速原型 |
| 监控协议 | SNMP v2c | 兼容绝大多数网络设备 |
| 前端图表 | Chart.js | 比 ECharts 更轻，够用 |
| 数据库 | SQLite | 免安装、单文件部署 |
| 后台任务 | Python threading | 轮询设备状态不阻塞 HTTP 服务 |

---

## 三个核心功能

### 1. 设备自动发现

用户输入 IP 段（如 192.168.1.0/24），系统后台线程逐 IP 发送 ICMP ping，能 ping 通就加入设备列表。对于支持 SNMP 的设备，自动尝试 community string 获取设备名和端口信息。

### 2. 实时监控 + 数据采集

每隔 5 分钟（可配置），后台线程对所有已发现设备进行：ICMP 延迟测试、SNMP 获取 CPU/内存、SNMP 获取交换机端口流量。数据存入 SQLite，前端通过 Chart.js 展示 24 小时趋势图。

### 3. 异常告警

如果某设备连续 3 次 ping 不通，或 CPU/内存超过阈值（默认 80%），触发告警。告警信息在面板顶部红点提示，同时支持 CSV 导出以便运维报告。

---

## 踩过的坑

**SNMP OID 适配**：不同厂商的设备 OID 不完全一致——华为和思科的 CPU OID 就不同。解决办法是定义 OID 模板，设备创建时可选"厂商"参数，自动匹配对应的 OID 集合。

**多线程安全**：后台监控线程和 Flask-WSGI 请求线程共享设备列表。用 `threading.Lock` 保护读写操作，避免竞态。

**Chart.js 大数据量**：24 小时数据 x 每分钟一个点 = 1440 个数据点。Chart.js 在移动端渲染会卡。通过降采样（5 分钟粒度） + `spanGaps` 解决了这个问题。

---

## 写在最后

这个毕设项目让我完整经历了一个全栈项目的生命周期：需求分析 → 技术选型 → 数据库设计 → 前后端联调 → 实际部署测试。最重要的是学会了在约束条件下做取舍——比如选 SQLite 而不是 MySQL（部署简单）、选 SNMP v2c 而不是 v3（设备兼容性更好）。

源码：[GitHub](https://github.com/lzn956827063-create/-)
"""

NETWORK_HTML = render_markdown(NETWORK_BLOG_MD)
NETWORK_EXCERPT = extract_excerpt(NETWORK_BLOG_MD, NETWORK_HTML, 400)

post2 = BlogService.create_post(
    title="内网监控面板：从零搭建企业级网络设备监控系统",
    slug="network-monitor-building",
    content_md=NETWORK_BLOG_MD,
    content_html=NETWORK_HTML,
    excerpt=NETWORK_EXCERPT,
    category_id=1,
    is_published=True,
)
print(f"Network Monitor blog: id={post2.id}, slug={post2.slug}")

ctx.pop()
print("\n=== DONE ===")

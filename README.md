# 企业内网实时监控系统

基于 Python Flask + SNMP 协议的企业级网络设备监控平台，毕业设计项目。

## 功能

- **设备自动发现** — ARP 表扫描 + ICMP Ping 自动发现局域网内活跃设备
- **SNMP 交换机监控** — 采集交换机端口流量、带宽利用率、包错误率等指标
- **实时性能采集** — 定时轮询设备延迟（ICMP RTT）、CPU 使用率、内存占用
- **异常检测告警** — 可配置阈值，超过阈值自动标记异常并记录告警历史
- **可视化面板** — Chart.js 渲染实时趋势曲线与设备级历史图表
- **数据导出** — 支持导出 CSV 格式历史数据

## 技术栈

- **后端**：Python 3 + Flask
- **协议**：SNMP v2c（pysnmp）
- **前端**：Bootstrap 5 + Chart.js
- **数据库**：SQLite
- **系统监控**：psutil、ICMP Ping

## 快速开始

```bash
# 安装依赖
pip install flask psutil pysnmp

# 启动监控系统
python monitor.py
```

访问 http://127.0.0.1:5000 查看监控面板。

## 项目结构

```
network_monitor/
├── monitor.py               # 主监控程序（Flask Web 服务）
├── switch_snmp_monitor.py   # SNMP 交换机监控
├── database.py              # SQLite 数据库操作
├── anomaly.py               # 异常检测模块
├── devices.py               # 设备自动发现
├── templates/               # HTML 模板
│   ├── index.html           # 监控面板主页
│   └── switches.html        # 交换机监控页
└── static/
    └── chart.js             # 前端图表配置
```

## License

MIT

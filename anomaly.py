
def detect_anomaly(status, thresholds):
    anomalies = []

    if status["delay"] is None:
        anomalies.append("设备离线")
    elif status["delay"] > thresholds["delay_ms"]:
        anomalies.append("网络延迟过高")

    if status["cpu"] > thresholds["cpu"]:
        anomalies.append("CPU 使用率异常")

    if status["memory"] > thresholds["memory"]:
        anomalies.append("内存使用率异常")

    return anomalies


def detect_switch_anomaly(snapshot, thresholds):
    anomalies = []
    # 1. 离线检查
    if not snapshot.get("reachable"):
        return ["交换机无法访问 (SNMP 无响应)"]

    # 2. 接口 Down 警告（管理状态为 up，运行状态为 down）
    for iface in snapshot.get("interfaces", []):
        if iface.get("admin_status") == "up" and iface.get("oper_status") == "down":
            anomalies.append(f"接口 {iface['name']} (Index:{iface.get('index', '?')}) 异常关闭")

    # 3. 检查 CPU
    cpu = snapshot.get("cpu_usage")  # 需确保采集到了此数据
    if cpu is not None and cpu > thresholds.get("switch_cpu", 85):
        anomalies.append(f"交换机 CPU 使用率异常 ({cpu}%)")

    # 4. 检查丢包率（百分比）
    packet_loss = snapshot.get("packet_loss")
    if packet_loss is not None and packet_loss > thresholds.get("max_loss", 5):
        anomalies.append(f"检测到高丢包率 ({packet_loss}%)")

    return anomalies
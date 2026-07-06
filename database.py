import sqlite3
from datetime import datetime

DB_NAME = "monitor_data.db"


def _get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS device_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            delay REAL,
            cpu REAL,
            memory REAL,
            anomalies TEXT,
            timestamp DATETIME
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS device_metadata (
            ip TEXT PRIMARY KEY,
            alias TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            updated_at DATETIME
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_devices (
            ip TEXT PRIMARY KEY,
            created_at DATETIME
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS switch_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            delay REAL,
            packet_loss REAL,
            cpu REAL,
            anomalies TEXT,
            timestamp DATETIME
        )
        """
    )
    conn.commit()
    conn.close()


def save_metric(ip, delay, cpu, memory, anomalies):
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        anomaly_str = ",".join(anomalies) if anomalies else ""
        cursor.execute(
            """
            INSERT INTO device_metrics (ip, delay, cpu, memory, anomalies, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ip, delay, cpu, memory, anomaly_str, datetime.now()),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[Database Error] {exc}")


def get_history(ip, limit=50):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT delay, cpu, memory, anomalies, timestamp
        FROM device_metrics
        WHERE ip = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (ip, limit),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_recent_alerts(limit=50):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, ip, anomalies, timestamp, delay, cpu, memory
        FROM device_metrics
        WHERE anomalies IS NOT NULL AND anomalies != ''
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = []
    for row in cursor.fetchall():
        item = dict(row)
        item["anomalies"] = item["anomalies"].split(",") if item["anomalies"] else []
        rows.append(item)
    conn.close()
    return rows


def get_recent_alerts_filtered(limit=50, query=""):
    conn = _get_connection()
    cursor = conn.cursor()
    sql = """
        SELECT id, ip, anomalies, timestamp, delay, cpu, memory
        FROM device_metrics
        WHERE anomalies IS NOT NULL AND anomalies != ''
    """
    params = []
    if query:
        sql += " AND (ip LIKE ? OR anomalies LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like])
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    cursor.execute(sql, params)
    rows = []
    for row in cursor.fetchall():
        item = dict(row)
        item["anomalies"] = item["anomalies"].split(",") if item["anomalies"] else []
        rows.append(item)
    conn.close()
    return rows


def upsert_device_metadata(ip, alias="", note=""):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO device_metadata (ip, alias, note, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ip) DO UPDATE SET
            alias = excluded.alias,
            note = excluded.note,
            updated_at = excluded.updated_at
        """,
        (ip, alias.strip(), note.strip(), datetime.now()),
    )
    conn.commit()
    conn.close()


def get_device_metadata(ip):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ip, alias, note, updated_at
        FROM device_metadata
        WHERE ip = ?
        """,
        (ip,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_device_metadata():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ip, alias, note, updated_at
        FROM device_metadata
        """
    )
    rows = {row["ip"]: dict(row) for row in cursor.fetchall()}
    conn.close()
    return rows


def get_metrics_for_export(ip=None, limit=1000):
    conn = _get_connection()
    cursor = conn.cursor()
    if ip:
        cursor.execute(
            """
            SELECT ip, delay, cpu, memory, anomalies, timestamp
            FROM device_metrics
            WHERE ip = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (ip, limit),
        )
    else:
        cursor.execute(
            """
            SELECT ip, delay, cpu, memory, anomalies, timestamp
            FROM device_metrics
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def add_manual_device(ip):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO manual_devices (ip, created_at)
        VALUES (?, ?)
        """,
        (ip, datetime.now()),
    )
    conn.commit()
    conn.close()


def remove_manual_device(ip):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM manual_devices
        WHERE ip = ?
        """,
        (ip,),
    )
    conn.commit()
    conn.close()


def get_manual_devices():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ip
        FROM manual_devices
        ORDER BY created_at ASC
        """
    )
    rows = [row["ip"] for row in cursor.fetchall()]
    conn.close()
    return rows


def save_switch_metric(ip, delay, packet_loss, cpu, anomalies):
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        anomaly_str = ",".join(anomalies) if anomalies else ""
        cursor.execute(
            """
            INSERT INTO switch_metrics (ip, delay, packet_loss, cpu, anomalies, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ip, delay, packet_loss, cpu, anomaly_str, datetime.now()),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        print(f"[Database Error] {exc}")


def get_recent_switch_alerts(limit=50, query=""):
    conn = _get_connection()
    cursor = conn.cursor()
    sql = """
        SELECT id, ip, anomalies, timestamp, delay, packet_loss, cpu
        FROM switch_metrics
        WHERE anomalies IS NOT NULL AND anomalies != ''
    """
    params = []
    if query:
        sql += " AND (ip LIKE ? OR anomalies LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like])
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    cursor.execute(sql, params)
    rows = []
    for row in cursor.fetchall():
        item = dict(row)
        item["anomalies"] = item["anomalies"].split(",") if item["anomalies"] else []
        rows.append(item)
    conn.close()
    return rows

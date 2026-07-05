import argparse
import asyncio
import json
import time

try:
    from pysnmp.hlapi import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
        getCmd,
        nextCmd,
    )
    SNMP_MODE = "legacy"
except ImportError:
    try:
        from pysnmp.hlapi.v1arch import (
            CommunityData,
            ObjectIdentity,
            ObjectType,
            SnmpDispatcher,
            UdpTransportTarget,
            get_cmd,
            next_cmd,
        )

        ContextData = None
        SnmpEngine = SnmpDispatcher
        getCmd = get_cmd
        nextCmd = next_cmd
        SNMP_MODE = "v1arch_asyncio"
    except ImportError:
        CommunityData = None
        ObjectIdentity = None
        ObjectType = None
        SnmpEngine = None
        UdpTransportTarget = None
        ContextData = None
        getCmd = None
        nextCmd = None
        SNMP_MODE = None


OIDS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "ifDescr": "1.3.6.1.2.1.2.2.1.2",
    "ifAdminStatus": "1.3.6.1.2.1.2.2.1.7",
    "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
    "ifSpeed": "1.3.6.1.2.1.2.2.1.5",
    "ifHCInOctets": "1.3.6.1.2.1.31.1.1.1.6",
    "ifHCOutOctets": "1.3.6.1.2.1.31.1.1.1.10",
    "ifAlias": "1.3.6.1.2.1.31.1.1.1.18",
}

STATUS_MAP = {
    1: "up",
    2: "down",
    3: "testing",
    4: "unknown",
    5: "dormant",
    6: "notPresent",
    7: "lowerLayerDown",
}


def _require_snmp():
    if not all((CommunityData, ObjectIdentity, ObjectType, SnmpEngine, UdpTransportTarget, getCmd, nextCmd)):
        raise RuntimeError("pysnmp is not available in this environment")


def _normalize_oid(oid):
    return oid.lstrip(".")


def _community_v2c(community):
    return CommunityData(community, mpModel=1)


def _parse_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_no_such_instance(value):
    text = value.prettyPrint() if hasattr(value, "prettyPrint") else str(value)
    return "No Such Instance" in text or "No Such Object" in text


def _ticks_to_text(value):
    ticks = _parse_int(value)
    total_seconds = ticks // 100
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"


def _build_transport_legacy(ip, port, timeout, retries):
    return UdpTransportTarget((ip, port), timeout=timeout, retries=retries)


async def _build_transport_async(ip, port, timeout, retries):
    return await UdpTransportTarget.create((ip, port), timeout=timeout, retries=retries)


async def _get_value_async(ip, oid, community, port, timeout, retries):
    transport = await _build_transport_async(ip, port, timeout, retries)
    error_indication, error_status, _, var_binds = await getCmd(
        SnmpEngine(),
        _community_v2c(community),
        transport,
        ObjectType(ObjectIdentity(_normalize_oid(oid))),
    )
    if error_indication or error_status:
        return None
    for _, value in var_binds:
        return value
    return None


async def _walk_async(ip, oid_prefix, community, port, timeout, retries):
    values = []
    transport = await _build_transport_async(ip, port, timeout, retries)
    current_oid = _normalize_oid(oid_prefix)
    dispatcher = SnmpEngine()

    while True:
        error_indication, error_status, _, var_binds = await nextCmd(
            dispatcher,
            _community_v2c(community),
            transport,
            ObjectType(ObjectIdentity(current_oid)),
        )
        if error_indication or error_status or not var_binds:
            return values

        advanced = False
        for oid, value in var_binds:
            pretty_oid = oid.prettyPrint()
            if not pretty_oid.startswith(_normalize_oid(oid_prefix)):
                return values
            values.append((pretty_oid, value))
            parts = pretty_oid.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            current_oid = ".".join(parts)
            advanced = True
        if not advanced:
            return values


def snmp_get(ip, oid, community="public", port=161, timeout=1, retries=1):
    _require_snmp()
    try:
        if SNMP_MODE == "v1arch_asyncio":
            return asyncio.run(_get_value_async(ip, oid, community, port, timeout, retries))

        iterator = getCmd(
            SnmpEngine(),
            _community_v2c(community),
            _build_transport_legacy(ip, port, timeout, retries),
            ContextData(),
            ObjectType(ObjectIdentity(_normalize_oid(oid))),
        )
        error_indication, error_status, _, var_binds = next(iterator)
        if error_indication or error_status:
            return None
        for _, value in var_binds:
            return value
    except Exception:
        return None
    return None


def snmp_walk(ip, oid_prefix, community="public", port=161, timeout=1, retries=1):
    _require_snmp()
    try:
        if SNMP_MODE == "v1arch_asyncio":
            return asyncio.run(_walk_async(ip, oid_prefix, community, port, timeout, retries))

        values = []
        for error_indication, error_status, _, var_binds in nextCmd(
            SnmpEngine(),
            _community_v2c(community),
            _build_transport_legacy(ip, port, timeout, retries),
            ContextData(),
            ObjectType(ObjectIdentity(_normalize_oid(oid_prefix))),
            lexicographicMode=False,
        ):
            if error_indication or error_status:
                return values
            for oid, value in var_binds:
                if not oid.prettyPrint().startswith(_normalize_oid(oid_prefix)):
                    return values
                values.append((oid.prettyPrint(), value))
        return values
    except Exception:
        return []


def _walk_indexed(ip, oid_prefix, **kwargs):
    result = {}
    for oid, value in snmp_walk(ip, oid_prefix, **kwargs):
        index = oid.rsplit(".", 1)[-1]
        result[index] = value.prettyPrint() if hasattr(value, "prettyPrint") else str(value)
    return result


def _sample_counters(ip, community, port, timeout, retries):
    in_values = _walk_indexed(ip, OIDS["ifHCInOctets"], community=community, port=port, timeout=timeout, retries=retries)
    if not in_values:
        in_values = _probe_indexed_table(ip, OIDS["ifHCInOctets"], community, port, timeout, retries)

    out_values = _walk_indexed(ip, OIDS["ifHCOutOctets"], community=community, port=port, timeout=timeout, retries=retries)
    if not out_values:
        out_values = _probe_indexed_table(ip, OIDS["ifHCOutOctets"], community, port, timeout, retries)

    return {
        "in": in_values,
        "out": out_values,
        "ts": time.time(),
    }


def _rate_mbps(new_value, old_value, seconds):
    if seconds <= 0:
        return 0.0
    delta = _parse_int(new_value) - _parse_int(old_value)
    if delta < 0:
        return 0.0
    return round((delta * 8) / seconds / 1_000_000, 4)


def _probe_indexed_table(ip, oid_prefix, community, port, timeout, retries, start=1, end=48, max_misses=6):
    result = {}
    misses = 0
    for index in range(start, end + 1):
        value = snmp_get(
            ip,
            f"{oid_prefix}.{index}",
            community=community,
            port=port,
            timeout=timeout,
            retries=retries,
        )
        if value is None:
            misses += 1
            if misses >= max_misses and result:
                break
            continue
        if _is_no_such_instance(value):
            misses += 1
            if misses >= max_misses and result:
                break
            continue
        misses = 0
        result[str(index)] = value.prettyPrint() if hasattr(value, "prettyPrint") else str(value)
    return result


def fetch_switch_snapshot(ip, community="public", port=161, timeout=1, retries=1, interval=3):
    sys_name = snmp_get(ip, OIDS["sysName"], community, port, timeout, retries)
    sys_descr = snmp_get(ip, OIDS["sysDescr"], community, port, timeout, retries)
    sys_uptime_raw = snmp_get(ip, OIDS["sysUpTime"], community, port, timeout, retries)
    has_system_data = any(item is not None for item in (sys_name, sys_descr, sys_uptime_raw))

    if not has_system_data:
        return {"ip": ip, "reachable": False, "error": "snmp_no_response", "interfaces": []}

    system = {
        "ip": ip,
        "sysName": str(sys_name or ""),
        "sysDescr": str(sys_descr or ""),
        "sysUpTime": _ticks_to_text(sys_uptime_raw or 0),
    }

    descrs = _walk_indexed(ip, OIDS["ifDescr"], community=community, port=port, timeout=timeout, retries=retries)
    if not descrs:
        descrs = _probe_indexed_table(ip, OIDS["ifDescr"], community, port, timeout, retries)

    admin = _walk_indexed(ip, OIDS["ifAdminStatus"], community=community, port=port, timeout=timeout, retries=retries)
    if not admin:
        admin = _probe_indexed_table(ip, OIDS["ifAdminStatus"], community, port, timeout, retries)

    oper = _walk_indexed(ip, OIDS["ifOperStatus"], community=community, port=port, timeout=timeout, retries=retries)
    if not oper:
        oper = _probe_indexed_table(ip, OIDS["ifOperStatus"], community, port, timeout, retries)

    speed = _walk_indexed(ip, OIDS["ifSpeed"], community=community, port=port, timeout=timeout, retries=retries)
    if not speed:
        speed = _probe_indexed_table(ip, OIDS["ifSpeed"], community, port, timeout, retries)

    alias = _walk_indexed(ip, OIDS["ifAlias"], community=community, port=port, timeout=timeout, retries=retries)
    if not alias:
        alias = _probe_indexed_table(ip, OIDS["ifAlias"], community, port, timeout, retries)

    counters_before = _sample_counters(ip, community, port, timeout, retries)
    time.sleep(interval)
    counters_after = _sample_counters(ip, community, port, timeout, retries)
    seconds = max(counters_after["ts"] - counters_before["ts"], 0.001)

    interfaces = []
    for index in sorted(descrs, key=lambda item: int(item)):
        in_old = counters_before["in"].get(index, "0")
        out_old = counters_before["out"].get(index, "0")
        in_new = counters_after["in"].get(index, "0")
        out_new = counters_after["out"].get(index, "0")
        admin_status = _parse_int(admin.get(index))
        oper_status = _parse_int(oper.get(index))
        interfaces.append(
            {
                "index": int(index),
                "name": descrs.get(index, ""),
                "alias": alias.get(index, ""),
                "admin_status": STATUS_MAP.get(admin_status, str(admin_status)),
                "oper_status": STATUS_MAP.get(oper_status, str(oper_status)),
                "speed_bps": _parse_int(speed.get(index)),
                "in_mbps": _rate_mbps(in_new, in_old, seconds),
                "out_mbps": _rate_mbps(out_new, out_old, seconds),
                "in_octets": _parse_int(in_new),
                "out_octets": _parse_int(out_new),
            }
        )

    return {
        "ip": ip,
        "reachable": True,
        "system": system,
        "interfaces": interfaces,
    }


def main():
    parser = argparse.ArgumentParser(description="Standalone SNMP v2c switch monitor")
    parser.add_argument("ips", nargs="+", help="Switch IP addresses")
    parser.add_argument("--community", default="public", help="SNMP v2c community")
    parser.add_argument("--port", type=int, default=161, help="SNMP port")
    parser.add_argument("--timeout", type=float, default=1.0, help="Per-request timeout in seconds")
    parser.add_argument("--retries", type=int, default=1, help="SNMP retries")
    parser.add_argument("--interval", type=int, default=3, help="Counter sampling interval in seconds")
    args = parser.parse_args()

    payload = {
        "snmp_mode": SNMP_MODE,
        "community": args.community,
        "results": [
            fetch_switch_snapshot(
                ip,
                community=args.community,
                port=args.port,
                timeout=args.timeout,
                retries=args.retries,
                interval=args.interval,
            )
            for ip in args.ips
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Telemetry Sample Generator & Ingestion Tester Script

Purpose:
    Generates realistic telemetry payloads matching assignment specification
    and posts them to the local Flask backend telemetry APIs.

Usage:
    python scripts/generate_telemetry.py [--count 10] [--target http://127.0.0.1:5000/api/v1/telemetry] [--bulk]
"""

import argparse
import random
import sys
import time
import requests
from datetime import datetime, timezone

DEFAULT_TARGET = "http://127.0.0.1:5000/api/v1/telemetry"
EVENTS = ["heartbeat", "power_lost", "power_restored", "boot"]
FIRMWARES = ["1.4.0", "1.4.2", "2.0.1"]


def parse_args():
    parser = argparse.ArgumentParser(description="Generate and post sample telemetry data to backend.")
    parser.add_argument("--count", type=int, default=5, help="Number of telemetry packets to generate (default: 5)")
    parser.add_argument("--target", default=DEFAULT_TARGET, help=f"Target API endpoint URL (default: {DEFAULT_TARGET})")
    parser.add_argument("--bulk", action="store_true", help="Post payloads in a single bulk array request")
    parser.add_argument("--device-id", default=None, help="Custom device ID")
    parser.add_argument("--pole-id", default=None, help="Custom pole code")
    return parser.parse_args()


def generate_packet(seq: int, device_id: str = None, pole_id: str = None, event: str = None):
    dev = device_id or f"KSPDB-SD07-D0112-{(seq % 50) + 1:04d}"
    pole = pole_id or f"POL-NORTH-01-{(seq % 50) + 1:03d}"
    evt = event or random.choice(EVENTS)
    energized = False if evt == "power_lost" else True

    return {
        "device_id": dev,
        "pole_id": pole,
        "event": evt,
        "energized": energized,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "seq": seq,
        "battery_mv": random.randint(3400, 4200),
        "rssi": random.randint(-95, -50),
        "fw": random.choice(FIRMWARES)
    }


def main():
    args = parse_args()
    print(f"======================================================")
    print(f"   Telemetry Generator & Ingestion Testing Tool       ")
    print(f"======================================================")
    print(f"Target Endpoint : {args.target}")
    print(f"Packet Count    : {args.count}")
    print(f"Mode            : {'BULK ARRAY' if args.bulk else 'SINGLE PAYLOADS'}")
    print(f"======================================================")

    if args.bulk:
        bulk_url = args.target if args.target.endswith("/bulk") else f"{args.target.rstrip('/')}/bulk"
        payloads = [generate_packet(seq=1000 + i, device_id=args.device_id, pole_id=args.pole_id) for i in range(args.count)]
        print(f"Posting {len(payloads)} items to {bulk_url}...")
        try:
            res = requests.post(bulk_url, json=payloads, timeout=10)
            print(f"Status Code: {res.status_code}")
            print(f"Response   : {res.text}")
        except Exception as e:
            print(f"Error submitting request: {e}")
    else:
        single_url = args.target.rstrip('/')
        if single_url.endswith("/bulk"):
            single_url = single_url[:-5]

        for i in range(1, args.count + 1):
            packet = generate_packet(seq=i, device_id=args.device_id, pole_id=args.pole_id)
            try:
                res = requests.post(single_url, json=packet, timeout=5)
                print(f"[{i}/{args.count}] Status {res.status_code} | Seq #{packet['seq']} | Event '{packet['event']}' | Resp: {res.json().get('status')}")
            except Exception as e:
                print(f"[{i}/{args.count}] Request Error: {e}")
            time.sleep(0.1)

    print("Telemetry generation complete.")


if __name__ == "__main__":
    main()

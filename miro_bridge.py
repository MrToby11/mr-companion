#!/usr/bin/env python3
"""
miro_bridge.py — MiRo ROS bridge service.

Runs inside a Docker container with ROS Noetic installed.
Connects to the MiRo simulator via ROS topics and exposes a simple
HTTP API on port 5001 so the FastAPI app can control the robot
without needing ROS on the main server.

Endpoints:
  GET  /battery  → {"voltage": 7.4, "percent": 85}
  POST /alert    → {"ok": true}

Start manually (after sourcing ROS):
  MIRO_ROBOT_NAME=sim01 python3 miro_bridge.py

Or via Docker:
  docker build -f Dockerfile.miro -t miro-bridge .
  docker run --rm -p 5001:5001 miro-bridge
"""

import os
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

import rospy
import std_msgs.msg

# Battery voltage range for MiRo-E (volts)
_BATTERY_MIN_V = 6.5
_BATTERY_MAX_V = 8.35

ROBOT_NAME = os.environ.get("MIRO_ROBOT_NAME", "sim01")
TOPIC_BASE = "/" + ROBOT_NAME

_lock = threading.Lock()
_battery_voltage = None  # updated by ROS callback

_pub_illum = None
_pub_tone = None


def _voltage_to_percent(v: float) -> int:
    pct = (v - _BATTERY_MIN_V) / (_BATTERY_MAX_V - _BATTERY_MIN_V) * 100
    return max(0, min(100, int(round(pct))))


def _cb_sensors(msg):
    global _battery_voltage
    with _lock:
        _battery_voltage = float(msg.battery.voltage)


def _trigger_alert():
    """Flash all LEDs red and play a 440 Hz warning tone for 1 second."""
    if _pub_illum:
        illum = std_msgs.msg.UInt32MultiArray()
        # Format: 0xBBRRGGBB — brightness=0xFF, R=0xFF, G=0x00, B=0x00
        illum.data = [0xFFFF0000] * 6
        _pub_illum.publish(illum)

    if _pub_tone:
        tone = std_msgs.msg.UInt16MultiArray()
        # [frequency_hz, duration_ms, volume_0_255]
        tone.data = [440, 1000, 200]
        _pub_tone.publish(tone)


class _Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # suppress default access log noise

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/battery":
            self._json(404, {"error": "not found"})
            return

        with _lock:
            v = _battery_voltage

        if v is None:
            self._json(503, {"error": "no sensor data received from simulator yet"})
        else:
            self._json(200, {"voltage": round(v, 2), "percent": _voltage_to_percent(v)})

    def do_POST(self):
        if self.path != "/alert":
            self._json(404, {"error": "not found"})
            return

        _trigger_alert()
        self._json(200, {"ok": True})


def main():
    global _pub_illum, _pub_tone

    rospy.init_node("miro_bridge", anonymous=False)

    import miro2 as miro

    rospy.Subscriber(
        TOPIC_BASE + "/sensors/package",
        miro.msg.sensors_package,
        _cb_sensors,
        queue_size=1,
        tcp_nodelay=True,
    )

    _pub_illum = rospy.Publisher(
        TOPIC_BASE + "/control/illum",
        std_msgs.msg.UInt32MultiArray,
        queue_size=0,
    )
    _pub_tone = rospy.Publisher(
        TOPIC_BASE + "/control/tone",
        std_msgs.msg.UInt16MultiArray,
        queue_size=0,
    )

    time.sleep(1)
    print(f"MiRo bridge connected | robot='{ROBOT_NAME}' | listening on :5001")

    server = HTTPServer(("0.0.0.0", 5001), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    rospy.spin()
    server.shutdown()


if __name__ == "__main__":
    main()

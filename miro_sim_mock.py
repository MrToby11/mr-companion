#!/usr/bin/env python3
"""
miro_sim_mock.py — Lightweight MiRo simulator mock.

Publishes fake sensor data on the same ROS topics the real Gazebo simulator
would, so the bridge can be tested without installing Gazebo.

Publishes:
  /{robot}/sensors/package  — battery voltage oscillating around ~7.8 V

Subscribes (and logs):
  /{robot}/control/illum    — LED commands sent by the bridge
  /{robot}/control/tone     — tone commands sent by the bridge
"""

import math
import os
import time

import rospy
import std_msgs.msg

import miro2 as miro

ROBOT_NAME = os.environ.get("MIRO_ROBOT_NAME", "sim01")
TOPIC_BASE = "/" + ROBOT_NAME


def cb_illum(msg):
    colors = [hex(v) for v in msg.data]
    print(f"[mock] LED alert received: {colors}")


def cb_tone(msg):
    print(f"[mock] Tone alert received: freq={msg.data[0]} Hz  dur={msg.data[1]} ms  vol={msg.data[2]}")


def main():
    rospy.init_node("miro_sim_mock", anonymous=False)

    pub = rospy.Publisher(
        TOPIC_BASE + "/sensors/package",
        miro.msg.sensors_package,
        queue_size=1,
    )

    rospy.Subscriber(TOPIC_BASE + "/control/illum", std_msgs.msg.UInt32MultiArray, cb_illum)
    rospy.Subscriber(TOPIC_BASE + "/control/tone",  std_msgs.msg.UInt16MultiArray, cb_tone)

    print(f"Mock simulator running | robot='{ROBOT_NAME}' | publishing at 50 Hz")

    rate = rospy.Rate(50)  # match the real robot's publish rate
    t = 0.0
    while not rospy.is_shutdown():
        msg = miro.msg.sensors_package()
        # Battery oscillates gently between ~7.5 V and ~8.1 V
        msg.battery.voltage = 7.8 + 0.3 * math.sin(t * 0.05)
        pub.publish(msg)
        t += 1.0 / 50.0
        rate.sleep()


if __name__ == "__main__":
    main()

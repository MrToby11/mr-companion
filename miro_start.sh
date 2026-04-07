#!/bin/bash
# miro_start.sh — starts roscore, mock simulator, and bridge inside the container.

source /opt/ros/noetic/setup.bash
source /mdk/catkin_ws/install/setup.bash
export PYTHONPATH=/mdk/share/python:$PYTHONPATH

echo "Starting roscore..."
roscore &
sleep 3

echo "Starting mock simulator..."
python3 /app/miro_sim_mock.py &
sleep 2

echo "Starting MiRo bridge..."
python3 /app/miro_bridge.py

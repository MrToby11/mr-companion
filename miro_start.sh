#!/bin/bash
# miro_start.sh — starts roscore, mock simulator, and bridge inside the container.

source /opt/ros/noetic/setup.bash
source /mdk/catkin_ws/install/setup.bash || true

# Set PYTHONPATH explicitly in case catkin setup had permission issues
export PYTHONPATH=/mdk/share/python:/mdk/catkin_ws/install/lib/python3/dist-packages:$PYTHONPATH

echo "Starting roscore..."
roscore &
sleep 3

echo "Starting mock simulator..."
python3 /app/miro_sim_mock.py &
sleep 2

echo "Starting MiRo bridge..."
python3 /app/miro_bridge.py

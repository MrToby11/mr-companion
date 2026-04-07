#!/bin/bash
# miro_start.sh — starts roscore, mock simulator, and bridge inside the container.

source /opt/ros/noetic/setup.bash
source /mdk/catkin_ws/install/setup.bash || true

export PYTHONPATH=/mdk/share/python:/mdk/catkin_ws/install/lib/python3/dist-packages:$PYTHONPATH
export PYTHONUNBUFFERED=1
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost

echo "[1/3] Starting roscore..."
roscore &
ROSCORE_PID=$!
echo "      roscore PID: $ROSCORE_PID"

# Wait until rosmaster is accepting connections before starting nodes
echo "      Waiting for rosmaster..."
for i in $(seq 1 30); do
    rostopic list > /dev/null 2>&1 && break
    sleep 1
    echo "      ...still waiting ($i/30)"
done
echo "      rosmaster ready."

echo "[2/3] Starting mock simulator..."
python3 -u /app/miro_sim_mock.py &
sleep 3

echo "[3/3] Starting MiRo bridge..."
python3 -u /app/miro_bridge.py

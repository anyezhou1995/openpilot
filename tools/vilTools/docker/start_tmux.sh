#!/bin/bash

tmux new -d -s sim
tmux send-keys "./docker/start_openpilot.sh" ENTER
tmux neww
tmux send-keys "alias k='tmux kill-server'" ENTER
tmux send-keys "python joybridge.py $*" ENTER
tmux a -t sim

#!/bin/bash

# expose X to the container
xhost +local:root

#docker pull ghcr.io/commaai/openpilot-sim:latest

OPENPILOT_DIR="/home/batman/openpilot"

CURRENT_DIR=$(pwd)

docker kill openpilot_client || true

export SIM_MODE="$1"

if [ "$SIM_MODE" == "sil" ]
then
    docker run --net=host\
    --privileged \
    --volume /dev/bus/usb:/dev/bus/usb \
    --volume /var/run/dbus:/var/run/dbus \
    --name openpilot_client \
    --rm \
    -it \
    --gpus all \
    --device=/dev/dri:/dev/dri \
    --device=/dev/input:/dev/input \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $CURRENT_DIR:$OPENPILOT_DIR/tools/wd \
    --shm-size 1G \
    -e DISPLAY=$DISPLAY \
    -e SIM_MODE=$SIM_MODE \
    -e QT_X11_NO_MITSHM=1 \
    -w "$OPENPILOT_DIR/tools/wd" \
    $EXTRA_ARGS \
    openpilot-96:latest \
    /bin/bash -c "./start_openpilot.sh ${@:2}"

elif [ "$SIM_MODE" == "hil" ]
then
    docker run --net=host\
    --privileged \
    --volume /dev/bus/usb:/dev/bus/usb \
    --volume /var/run/dbus:/var/run/dbus \
    --name openpilot_client \
    --rm \
    -it \
    --gpus all \
    --device=/dev/dri:/dev/dri \
    --device=/dev/input:/dev/input \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $CURRENT_DIR:$OPENPILOT_DIR/tools/wd \
    -v $(readlink -f "../../.git"):$OPENPILOT_DIR/.git \
    --shm-size 1G \
    -e DISPLAY=$DISPLAY \
    -e QT_X11_NO_MITSHM=1 \
    -e SIM_MODE=$SIM_MODE \
    -w "$OPENPILOT_DIR/tools/wd" \
    $EXTRA_ARGS \
    openpilot-96:latest \
    /bin/bash -c "./docker/start_tmux.sh ${@:2}"
else
    echo "No valid mode given"
fi

#!/bin/bash

OPENPILOT_DIR="/home/batman/openpilot"

if [[ "$SIM_MODE" == "sil" ]]
then
    export PASSIVE="0"
    export NOBOARD="1"
    export SIMULATION="1"
    export NOSENSOR="1"
    export FINGERPRINT="HONDA_CIVIC_2022"
    export BLOCK="${BLOCK},camerad,loggerd,encoderd,micd,logmessaged,soundd"

fi

if [[ "$SIM_MODE" == "hil" ]]
then
    export PASSIVE="0"
    export NOSENSOR="1"
    export SIMULATION="1"
    export BLOCK="${BLOCK},camerad,loggerd,encoderd,micd,logmessaged,soundd"

fi

if [[ "$CI" ]]; then
  # TODO: offscreen UI should work
  export BLOCK="${BLOCK},ui"
fi

python3 -c "from openpilot.selfdrive.test.helpers import set_params_enabled; set_params_enabled()"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

git config --global --add safe.directory /home/batman/openpilot
cd $OPENPILOT_DIR/system/manager && exec ./manager.py

#!/bin/bash

ip=${1#-}
rsync -avzP --delete . comma@$ip:/data/openpilot/tools/vilTools

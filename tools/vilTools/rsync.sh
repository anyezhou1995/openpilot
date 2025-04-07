#!/bin/bash

ip=${1#-}
# First copy the remote logs folder to local machine, deleting existing local copy if it exists
rsync -avzP --delete comma@$ip:/data/openpilot/tools/vilTools/logs ./local_logs_backup
# Then sync local tools to remote machine
rsync -avzP --delete . comma@$ip:/data/openpilot/tools/vilTools
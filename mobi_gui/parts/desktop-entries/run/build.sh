#!/bin/bash
set -euo pipefail
source /home/utk/mobi_ws/src/mobi_gui/parts/desktop-entries/run/environment.sh
set -x
cp --archive --link --no-dereference . "/home/utk/mobi_ws/src/mobi_gui/parts/desktop-entries/install"

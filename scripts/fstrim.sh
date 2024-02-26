#!/usr/bin/env bash

KUBELET_BIN="/usr/local/bin/kubelet"
KUBELET_PID="$(pgrep -f $KUBELET_BIN | head -n 1)"

if [ -z "${KUBELET_PID}" ]; then
    echo "kubelet not found"
    exit 1
fi

# Enter namespaces and run commands
nsrun() {
    nsenter \
        --mount="/proc/${KUBELET_PID}/ns/mnt" \
        --net="/proc/${KUBELET_PID}/ns/net" \
        -- bash -c "$1"
}


# Trim filesystems
nsrun "fstrim -v -a"

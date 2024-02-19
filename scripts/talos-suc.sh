#!/usr/bin/env bash

if [ -z "${NODE_IP}" ]; then
    echo "Error: NODE_IP env var is not set"
    exit 1
fi

if [ -n "${SETTLE_DOWN_SECONDS}" ]; then
    echo "Waiting for nodes to settle down for ${SETTLE_DOWN_SECONDS} seconds..."
    sleep "${SETTLE_DOWN_SECONDS}"
    echo "...Settle down complete"
fi

if [ "${TALOS_HEALTHCHECK:-true}" == "true" ]; then
    echo "Waiting for Talos to be healthy..."
    talosctl --nodes="${NODE_IP}" health --wait-timeout="${TALOS_TIMEOUT:-600s}" --server=false
    echo "...Talos is now healthy"
fi

if [ "${CEPH_HEALTHCHECK:-false}" == "true" ]; then
    echo "Waiting for Ceph to be healthy..."
    kubectl wait --timeout="${ROOK_TIMEOUT:-600s}" \
        --for=jsonpath=.status.ceph.health=HEALTH_OK cephcluster \
            --all --all-namespaces
    echo "...Ceph is now healthy"
fi

if [ "${CNPG_MAINTENANCE:-false}" == "true" ]; then
    echo "=== Setting CNPG maintenance mode ==="
    kubectl cnpg maintenance set --reusePVC --all-namespaces
fi

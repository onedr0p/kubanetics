#!/usr/bin/env bash

if [ -z "${ALERTMANAGER_URL}" ]; then
    echo "Error: ALERTMANAGER_URL env var is not set"
    exit 1
fi

for var in "${!MATCHERS_@}"; do
    value="${!var}"
    id=$(amtool --alertmanager.url="${ALERTMANAGER_URL}" silence query ${value} --output=json | jq --raw-output '.[].id')
    if [ -z "${id}" ]; then
        echo "Creating silence for ${value} ..."
        amtool --alertmanager.url="${ALERTMANAGER_URL}" silence add ${value} --author="Kubanetics" --comment="Silenced by Kubanetics" --duration=42069d
    else
        echo "Silence already exists for ${value} ..."
    fi
done

#!/usr/bin/env bash

if [ -z "${SCRIPT_NAME}" ]; then
    echo "Error: SCRIPT_NAME is not set. Exiting."
    exit 1
fi

if [ ! -f "/app/${SCRIPT_NAME}" ]; then
    echo "Error: Script '${SCRIPT_NAME}' not found in /app. Exiting."
    exit 1
fi

case "${SCRIPT_NAME}" in
    *.sh)
        echo "Running shell script: ${SCRIPT_NAME}"
        /bin/bash "/app/${SCRIPT_NAME}" "$@"
        ;;
    *.py)
        echo "Running python script: ${SCRIPT_NAME}"
        /usr/local/bin/python "/app/${SCRIPT_NAME}" "$@"
        ;;
    *)
        echo "Error: Unsupported script type: ${SCRIPT_NAME}. Exiting."
        exit 1
        ;;
esac

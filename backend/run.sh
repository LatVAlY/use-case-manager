#!/bin/bash

PROCESS=${PROCESS}

if [ "$PROCESS" = "worker" ]; then
    celery -A app.celery_app worker --loglevel=info
elif [ "$PROCESS" = "server" ]; then
    echo "running migrations"
    alembic upgrade head
    uvicorn app.main:app --reload --port 8000
else
    printf "Please specify the type of process to run: 'worker' or 'server'\n"
fi

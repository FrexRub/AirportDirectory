#!/bin/bash

#cd app/src

if [[ "${1}" == "celery" ]]; then
  .venv/bin/celery -A src.tasks.tasks:celery worker -l INFO
elif [[ "${1}" == "flower" ]]; then
  .venv/bin/celery -A src.tasks.tasks:celery flower
 fi

## скрипт для заруска по параметрам celery или flower

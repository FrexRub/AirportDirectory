#!/bin/bash

if [[ "${1}" == "celery" ]]; then
  celery -A src.tasks.celery_conf worker -l INFO
elif [[ "${1}" == "flower" ]]; then
  celery -A src.tasks.celery_conf flower
 fi

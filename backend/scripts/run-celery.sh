#!/bin/bash

celery -A worker.worker.celery_app worker --loglevel=info -Q agent
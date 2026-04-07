#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m networking_crm init-db
PYTHONPATH=src python3 -m networking_crm status

#!/bin/bash
# Monthly MOU Email Script for Linux/Mac
# This script activates the virtual environment and runs the Django management command

# Configuration
PROJECT_DIR="/path/to/your/project"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="/var/log/mou_emails.log"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source "$VENV_DIR/bin/activate" || exit 1

# Run the command and log output
echo "----------------------------------------" >> "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
python manage.py send_monthly_mou_emails >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
echo "Finished at: $(date)" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"

# Deactivate virtual environment
deactivate

exit $EXIT_CODE

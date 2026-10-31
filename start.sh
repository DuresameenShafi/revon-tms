#!/usr/bin/env bash
# macOS / Linux one-command start.  Usage: ./start.sh            (SQLite, zero setup)
#                                         MYSQL_PASSWORD=secret ./start.sh mysql
set -e
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
if [ "$1" = "mysql" ]; then export DB_ENGINE=mysql; python app.py --init-mysql; else export DB_ENGINE=sqlite; fi
python app.py

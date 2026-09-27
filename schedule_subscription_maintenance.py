"""Use your host scheduler every five minutes, with a process lock (see README)."""
from pathlib import Path
from datetime import datetime, timezone
import os
import sys
import subprocess

root = Path(__file__).resolve().parent
reports = Path(os.getenv('CREDIT_REPORT_DIR', str(root / 'instance' / 'credit_reports')))
reports.mkdir(parents=True, exist_ok=True, mode=0o700)
name = 'maintenance_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'
result = subprocess.run([sys.executable, '-m', 'flask', '--app', 'run', 'credits', 'maintain',
                         '--output', str((reports/name).resolve())], cwd=root)
raise SystemExit(result.returncode)

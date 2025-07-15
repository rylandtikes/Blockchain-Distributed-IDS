import sys
import os
os.environ["USE_TF"] = "0"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import subprocess
import time
from ids.host_ids.model_inference import classify_log_line
from ids.host_ids.prometheus_exporter import export_alert, start_exporter_server
import yaml

config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

def monitor_logs():
    start_exporter_server()
    print("Host-based IDS started. Monitoring logs from both user and system journals...")

    commands = [
        ['journalctl', '--user', '-o', 'short-iso', '-n', str(config["log_lines"]), '-f'],
        ['journalctl', '-o', 'short-iso', '-n', str(config["log_lines"]), '-f']
    ]

    processes = [
        subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
        for cmd in commands
    ]

    while True:
        for process in processes:
            line = process.stdout.readline()
            if not line:
                continue
            label, score = classify_log_line(line)
            if label == "POSITIVE" and score > config["alert_threshold"]:
                print(f"[ALERT] Suspicious log line: {line.strip()} ({score:.2f})")
                export_alert()


if __name__ == "__main__":
    monitor_logs()


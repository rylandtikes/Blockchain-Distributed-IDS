from prometheus_client import start_http_server, Counter

alert_counter = Counter('host_ids_alerts_total', 'Number of alerts triggered by host-based IDS')

def export_alert():
    alert_counter.inc()

def start_exporter_server(port=9102):
    start_http_server(port)


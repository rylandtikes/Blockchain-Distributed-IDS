from prometheus_client import start_http_server, Gauge
import time

start_http_server(9100)
test_metric = Gauge('test_metric_value', 'A test metric')

while True:
    test_metric.set(42)
    time.sleep(5)


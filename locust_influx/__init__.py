from datetime import datetime

from influxdb import InfluxDBClient
from locust import events, runners

influx_client = None


def make_record(measurement, tags, fields, time):
    return [{"measurement": measurement, "tags": tags, "time": time, "fields": fields}]


def ingest_data(influxdb_client, node_id):
    def save_to_influxdb(request_type=None, name=None, response_time=None, response_length=None, exception=None,
                         **kwargs):
        time = datetime.utcnow()
        tags = {
            'node_id': node_id
        }
        fields = {
            'request_type': request_type,
            'name': name,
            'response_time': response_time,
            'response_length': response_length,
            'exception': str(exception)
        }
        success = influxdb_client.write_points(make_record('request', tags, fields, time))
        if not success:
            print('Failed to save to InfluxDB')

    return save_to_influxdb


def expose_metrics(influx_host='localhost', influx_port=8086, user='root', pwd='root', db='locust'):
    influx_client = InfluxDBClient(influx_host, influx_port, user, pwd, db)
    influx_client.create_database(db)
    node_id = 'local'
    if runners.locust_runner:
        if runners.locust_runner.options.master:
            node_id = 'master'
        if runners.locust_runner.options.slave:
            node_id = runners.locust_runner.client_id

    events.request_success += ingest_data(influx_client, node_id)
    events.request_failure += ingest_data(influx_client, node_id)

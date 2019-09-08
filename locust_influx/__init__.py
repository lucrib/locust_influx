import logging
from datetime import datetime

from influxdb import InfluxDBClient
from locust import events, runners

__all__ = ['expose_metrics']

log = logging.getLogger('locust_influx')


def __make_record(measurement, tags, fields, time):
    return [{"measurement": measurement, "tags": tags, "time": time, "fields": fields}]


def __report_event(influxdb_client, node_id, event):
    def save_to_influxdb(**_):
        time = datetime.utcnow()
        tags = {
        }
        fields = {
            'node_id': node_id,
            'event': event
        }
        point = __make_record('locust_events', tags, fields, time)
        was_successful = influxdb_client.write_points(point)
        if not was_successful:
            log.error('Failed to save point to InfluxDB.')

    return save_to_influxdb


def __ingest_data(influxdb_client, node_id, measurement, success):
    def save_to_influxdb(request_type=None, name=None, response_time=None, response_length=None, exception=None, **_):
        time = datetime.utcnow()
        tags = {
            'node_id': node_id,
            'request_type': request_type,
            'name': name,
            'success': success,
            'exception': str(exception)
        }
        fields = {
            'response_time': response_time,
            'response_length': response_length,
            'counter': 1
        }
        point = __make_record(measurement, tags, fields, time)
        was_successful = influxdb_client.write_points(point)
        if not was_successful:
            log.error('Failed to save point to InfluxDB.')

    return save_to_influxdb


def expose_metrics(influx_host: str = 'localhost', influx_port: int = 8086, user: str = 'root', pwd: str = 'root',
                   database: str = 'locust', measurement: str = 'locust_requests'):
    influx_client = InfluxDBClient(influx_host, influx_port, user, pwd, database)
    influx_client.create_database(database)
    node_id = 'local'
    if runners.locust_runner:
        if runners.locust_runner.options.master:
            node_id = 'master'
        if runners.locust_runner.options.slave:
            node_id = runners.locust_runner.client_id
    # Request events
    events.request_success += __ingest_data(influx_client, node_id, measurement, success=True)
    events.request_failure += __ingest_data(influx_client, node_id, measurement, success=False)
    # Locust events
    events.hatch_complete += __report_event(influx_client, node_id, event='hatch_complete')
    events.quitting += __report_event(influx_client, node_id, event='quitting')
    events.master_start_hatching += __report_event(influx_client, node_id, event='master_start_hatching')
    events.master_stop_hatching += __report_event(influx_client, node_id, event='master_stop_hatching')
    events.locust_start_hatching += __report_event(influx_client, node_id, event='locust_start_hatching')
    events.locust_stop_hatching += __report_event(influx_client, node_id, event='locust_stop_hatching')

import logging
from datetime import datetime

from influxdb import InfluxDBClient
from locust import events, runners

__all__ = ['expose_metrics']

log = logging.getLogger('locust_influx')


def __make_record(measurement: str, tags: dict, fields: dict, time: datetime):
    """
    Create a list with a single point to be saved to influxdb.

    :param measurement: The measurement where to save this point.
    :param tags: Dictionary of tags to be saved in the measurement.
    :param fields: Dictionary of field to be saved to measurement.
    :param time: The time os this point.
    """
    return [{"measurement": measurement, "tags": tags, "time": time, "fields": fields}]


def __persist_event_info(influxdb_client: InfluxDBClient, node_id: str, event: str):
    """
    Persist locust event such as hatching started or stopped to influxdb.

    :param influxdb_client: InfluxDB instance to be used to save the event.
    :param node_id: The id of the node reporting the event.
    :param event: The event name or description.
    """

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


def __persist_request_info(influxdb_client, node_id, success, measurement: str = 'locust_requests'):
    """
    Persis request information to influxdb.

    :param influxdb_client: InfluxDB instance to be used to save the event.
    :param node_id: The id of the node reporting the event.
    :param measurement: The measurement where to save this point.
    :param success: Flag the info to as successful request or not
    """

    def save_to_influxdb(request_type=None, name=None, response_time=None, response_length=None, exception=None, **_):
        time = datetime.utcnow()
        tags = {
            'node_id': node_id,
            'request_type': request_type,
            'name': name,
            'success': success,
            'exception': str(exception),
        }
        fields = {
            'response_time': response_time,
            'response_length': response_length,
            'counter': 1,
        }
        point = __make_record(measurement, tags, fields, time)
        was_successful = influxdb_client.write_points(point)
        if not was_successful:
            log.error('Failed to save point to InfluxDB.')

    return save_to_influxdb


def expose_metrics(influx_host: str = 'localhost',
                   influx_port: int = 8086,
                   user: str = 'root',
                   pwd: str = 'root',
                   database: str = 'locust'):
    """
    Attach event handlers to locust EventHooks in order to persist information to influxdb.

    :param influx_host: InfluxDB hostname or IP.
    :param influx_port: InfluxDB port.
    :param user: InfluxDB username.
    :param pwd: InfluxDB password.
    :param database: InfluxDB database name. Will be created if not exist.
    """
    influx_client = InfluxDBClient(influx_host, influx_port, user, pwd, database)
    influx_client.create_database(database)
    node_id = 'local'
    if runners.locust_runner:
        if runners.locust_runner.options.master:
            node_id = 'master'
        if runners.locust_runner.options.slave:
            node_id = runners.locust_runner.client_id
    # Request events
    events.request_success += __persist_request_info(influx_client, node_id, success=True)
    events.request_failure += __persist_request_info(influx_client, node_id, success=False)
    # Locust events
    events.hatch_complete += __persist_event_info(influx_client, node_id, event='hatch_complete')
    events.quitting += __persist_event_info(influx_client, node_id, event='quitting')
    events.master_start_hatching += __persist_event_info(influx_client, node_id, event='master_start_hatching')
    events.master_stop_hatching += __persist_event_info(influx_client, node_id, event='master_stop_hatching')
    events.locust_start_hatching += __persist_event_info(influx_client, node_id, event='locust_start_hatching')
    events.locust_stop_hatching += __persist_event_info(influx_client, node_id, event='locust_stop_hatching')

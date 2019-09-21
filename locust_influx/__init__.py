import logging
import sys
import traceback
from datetime import datetime
from typing import Callable

import gevent
from influxdb import InfluxDBClient
from locust import events

__all__ = ['expose_metrics']

log = logging.getLogger('locust_influx')

cache = []
stop_flag = False


def __make_data_point(measurement: str, tags: dict, fields: dict, time: datetime):
    """
    Create a list with a single point to be saved to influxdb.

    :param measurement: The measurement where to save this point.
    :param tags: Dictionary of tags to be saved in the measurement.
    :param fields: Dictionary of field to be saved to measurement.
    :param time: The time os this point.
    """
    return {"measurement": measurement, "tags": tags, "time": time, "fields": fields}


def __listen_for_locust_events(node_id: str, event: str) -> Callable:
    """
    Persist locust event such as hatching started or stopped to influxdb.

    :param node_id: The id of the node reporting the event.
    :param event: The event name or description.
    """

    def event_handler(**_):
        time = datetime.utcnow()
        tags = {
        }
        fields = {
            'node_id': node_id,
            'event': event
        }
        point = __make_data_point('locust_events', tags, fields, time)
        cache.append(point)

    return event_handler


def __listen_for_requests_events(node_id, success, measurement: str = 'locust_requests') -> Callable:
    """
    Persist request information to influxdb.

    :param node_id: The id of the node reporting the event.
    :param measurement: The measurement where to save this point.
    :param success: Flag the info to as successful request or not
    """

    def event_handler(request_type=None, name=None, response_time=None, response_length=None, exception=None,
                      **_) -> None:
        time = datetime.utcnow()
        tags = {
            'node_id': node_id,
            'request_type': request_type,
            'name': name,
            'success': success,
            'exception': repr(exception),
        }
        fields = {
            'response_time': response_time,
            'response_length': response_length,
            'counter': 1,  # TODO: Review the need of this field
        }
        point = __make_data_point(measurement, tags, fields, time)
        cache.append(point)

    return event_handler


def __listen_for_locust_errors(node_id: str) -> Callable:
    """
    Persist locust errors to InfluxDB.

    :param node_id: The id of the node reporting the error.
    :return: None
    """

    def event_handler(exception: Exception = None, tb=None, **_) -> None:
        time = datetime.utcnow()
        tags = {
            'exception_tag': repr(exception),
        }
        fields = {
            'node_id': node_id,
            'exception': repr(exception),
            'traceback': "".join(traceback.format_tb(tb)),
        }
        point = __make_data_point('locust_exceptions', tags, fields, time)
        cache.append(point)

    return event_handler


def __flush_points(influxdb_client: InfluxDBClient) -> None:
    """
    Write the cached data points to influxdb

    :param influxdb_client: An instance of InfluxDBClient
    :return: None
    """
    global cache
    log.debug(f'Flushing points {len(cache)}')
    to_be_flushed = cache
    cache = []
    success = influxdb_client.write_points(to_be_flushed)
    if not success:
        log.error('Failed to write points to influxdb.')
        # If failed for any reason put back into the beginning of cache
        cache.insert(0, to_be_flushed)


def __flush_cached_points_worker(influxdb_client, interval) -> None:
    """
    Background job that puts the points into the cache to be flushed according tot he interval defined.

    :param influxdb_client:
    :param interval:
    :return: None
    """
    global stop_flag
    log.info('Flush worker started.')
    while not stop_flag:
        __flush_points(influxdb_client)
        gevent.sleep(interval / 1000)


def expose_metrics(influx_host: str = 'localhost',
                   influx_port: int = 8086,
                   user: str = 'root',
                   pwd: str = 'root',
                   database: str = 'locust',
                   interval_ms: int = 1000) -> None:
    """
    Attach event handlers to locust EventHooks in order to persist information to influxdb.

    :param influx_host: InfluxDB hostname or IP.
    :param influx_port: InfluxDB port.
    :param user: InfluxDB username.
    :param pwd: InfluxDB password.
    :param database: InfluxDB database name. Will be created if not exist.
    :param interval_ms: Interval to save the data points to influxdb.
    """
    influxdb_client = InfluxDBClient(influx_host, influx_port, user, pwd, database)
    influxdb_client.create_database(database)
    node_id = 'local'
    if '--master' in sys.argv:
        node_id = 'master'
    if '--slave' in sys.argv:
        # TODO: Get real ID of slaves form locust somehow
        node_id = 'slave'
    # Start a greenlet that will save the data to influx according to the interval informed
    flush_worker = gevent.spawn(__flush_cached_points_worker, influxdb_client, interval_ms)
    # Request events
    events.request_success += __listen_for_requests_events(node_id, success=True)
    events.request_failure += __listen_for_requests_events(node_id, success=False)
    # Locust events
    events.hatch_complete += __listen_for_locust_events(node_id, event='hatch_complete')
    events.quitting += __listen_for_locust_events(node_id, event='quitting')
    events.master_start_hatching += __listen_for_locust_events(node_id, event='master_start_hatching')
    events.master_stop_hatching += __listen_for_locust_events(node_id, event='master_stop_hatching')
    events.locust_start_hatching += __listen_for_locust_events(node_id, event='locust_start_hatching')
    events.locust_stop_hatching += __listen_for_locust_events(node_id, event='locust_stop_hatching')
    # Locust exceptions
    events.locust_error += __listen_for_locust_errors(node_id)

    def last_flush_on_quitting():
        global stop_flag
        stop_flag = True
        flush_worker.join()
        __flush_points(influxdb_client)

    # Flush last points when quiting
    events.quitting += last_flush_on_quitting

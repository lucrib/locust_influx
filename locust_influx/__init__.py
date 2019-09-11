import logging
import sys
from datetime import datetime

import gevent
from influxdb import InfluxDBClient
from locust import events

__all__ = ['expose_metrics']

log = logging.getLogger('locust_influx')


class BooleanFlag:
    def __init__(self, init_value: bool):
        self.__flag = init_value

    def __bool__(self):
        return self.__flag

    def set(self, new):
        self.__flag = new

    def get(self):
        return self.__flag


def __make_data_point(measurement: str, tags: dict, fields: dict, time: datetime):
    """
    Create a list with a single point to be saved to influxdb.

    :param measurement: The measurement where to save this point.
    :param tags: Dictionary of tags to be saved in the measurement.
    :param fields: Dictionary of field to be saved to measurement.
    :param time: The time os this point.
    """
    return {"measurement": measurement, "tags": tags, "time": time, "fields": fields}


def __listen_for_locust_events(cache: list, node_id: str, event: str):
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


def __listen_for_requests_events(cache, node_id, success, measurement: str = 'locust_requests'):
    """
    Persis request information to influxdb.

    :param node_id: The id of the node reporting the event.
    :param measurement: The measurement where to save this point.
    :param success: Flag the info to as successful request or not
    """

    def event_handler(request_type=None, name=None, response_time=None, response_length=None, exception=None, **_):
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
            'counter': 1,  # TODO: Review the need of this field
        }
        point = __make_data_point(measurement, tags, fields, time)
        cache.append(point)

    return event_handler


def __flush_points(influxdb_client: InfluxDBClient, cache: list):
    """
    Write the cached data points to influxdb

    :param influxdb_client: An instance of InfluxDBClient
    :param cache: The list holding the cached points to be flushed
    :return:
    """
    log.debug(f'Flushing points {len(cache)}')
    to_be_flushed = cache.copy()
    cache.clear()
    success = influxdb_client.write_points(to_be_flushed)
    if not success:
        log.error('Failed to write points to influxdb.')
        # If failed for any reason put back into the beginning of cache
        cache.insert(0, to_be_flushed)


def __flush_cached_points_worker(influxdb_client, interval, cache, stop_flag: BooleanFlag):
    log.info('Flush worker started.')
    while not stop_flag.get():
        __flush_points(influxdb_client, cache)
        gevent.sleep(interval / 1000)


def expose_metrics(influx_host: str = 'localhost',
                   influx_port: int = 8086,
                   user: str = 'root',
                   pwd: str = 'root',
                   database: str = 'locust',
                   interval_ms: int = 1000):
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
    cache = []
    finished = BooleanFlag(False)
    # Start a greenlet that will save the data to influx according to the interval
    flush_worker = gevent.spawn(__flush_cached_points_worker, influxdb_client, interval_ms, cache, finished)
    # Request events
    events.request_success += __listen_for_requests_events(cache, node_id, success=True)
    events.request_failure += __listen_for_requests_events(cache, node_id, success=False)
    # Locust events
    events.hatch_complete += __listen_for_locust_events(cache, node_id, event='hatch_complete')
    events.quitting += __listen_for_locust_events(cache, node_id, event='quitting')
    events.master_start_hatching += __listen_for_locust_events(cache, node_id, event='master_start_hatching')
    events.master_stop_hatching += __listen_for_locust_events(cache, node_id, event='master_stop_hatching')
    events.locust_start_hatching += __listen_for_locust_events(cache, node_id, event='locust_start_hatching')
    events.locust_stop_hatching += __listen_for_locust_events(cache, node_id, event='locust_stop_hatching')

    def last_flush_on_quitting():
        finished.set(True)
        flush_worker.join()
        __flush_points(influxdb_client, cache)
    # Flush last points when quiting
    events.quitting += last_flush_on_quitting()

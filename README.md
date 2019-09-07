# locust_influx

Send information about [locust](https://locust.io/) requests to influxdb.

Start a container of influxdb locally:

`docker run --hostname influxdb --name influxdb -d -p 8080:8086`

Start a container of grafana locally:

`docker run --hostname grafana --name grafana -d -p 3000:3000`

Create an example of `locustfile.py`

```python
from locust import TaskSet, HttpLocust, task

from locust_influx import expose_metrics

expose_metrics(influx_host='localhost',
               influx_port=8086)


class MyTasks(TaskSet):
    @task
    def get_index(self):
        self.client.post('/')

    @task
    def get_about(self):
        self.client.get('/about')


class GoogleLocust(HttpLocust):
    task_set = MyTasks
```

Run locust:

`locust -f ./locustfile.py --no-web --clients 10 --hatch-rate 1 --run-time 60s`

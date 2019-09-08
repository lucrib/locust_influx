# locust_influx

Send information about [locust](https://locust.io/) requests to influxdb.

Start a container of influxdb locally:

`docker run -d --name influxdb -d -p 8086:8086`

Start a container of grafana locally:

`docker run -d --name grafana -d -p 3000:3000`

Crete a new python venv:

`pip install locust_influx`

Create a test `locustfile.py`

```python
from locust import TaskSet, HttpLocust, task

from locust_influx import expose_metrics

expose_metrics()


class MyTasks(TaskSet):

    @task
    def get_home(self):
        self.client.get('/')

    @task
    def head_home(self):
        self.client.head('/')

    @task
    def delete_home(self):
        self.client.delete('/')

    @task
    def post_home(self):
        self.client.post('/.')

    @task
    def put_home(self):
        self.client.put('/')


class MyLocust(HttpLocust):
    task_set = MyTasks
```

Run locust (Change the host to point to desired one):

`locust -f ./locustfile.py --no-web --clients 10 --hatch-rate 1 --run-time 60s --host http://localhost:8080`

Open your local grafana in the browser at http://localhost:3000/

Import new dashboard from locust_dashboard.json file.

![Locust dashboard in grafana](https://raw.githubusercontent.com/lucrib/locust_influx/master/dashboard.png)

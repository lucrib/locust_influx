from random import randint

from locust import TaskSet, HttpLocust, task

from locust_influx import expose_metrics

expose_metrics(interval_ms=2000)


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
        self.client.post('/')

    @task
    def put_home(self):
        self.client.put('/')

    @task
    def cause_fail_get_request(self):
        n = randint(1, 3)
        self.client.get(f'/invalid-path-{n}')

    @task
    def cause_locust_error(self):
        raise Exception('Test Error')


class MyLocust(HttpLocust):
    task_set = MyTasks

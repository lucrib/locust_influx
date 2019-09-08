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

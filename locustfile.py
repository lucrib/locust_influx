from locust import TaskSet, HttpLocust, task

from locust_influx import expose_metrics

expose_metrics()


class GoogleTasks(TaskSet):
    min_wait = 1000
    max_wait = 1000

    @task
    def get_google_home(self):
        self.client.get('/')

    @task
    def do_google_search_fail(self):
        self.client.post('/complete/search?q=test')

    @task
    def do_google_search_success(self):
        self.client.get('/complete/search?q=test')


class GoogleLocust(HttpLocust):
    task_set = GoogleTasks
    host = 'https://www.google.com'


if __name__ == '__main__':
    expose_metrics()
    x = GoogleLocust()
    x.run()

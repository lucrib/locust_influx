# locust_influx

Send information about [locust](https://locust.io/) requests 
to [InfluxDB](https://www.influxdata.com/products/influxdb-overview/) 
and follow the progress through [Grafana](https://grafana.com/) charts.

## Test and taste it locally

Start an InfluxDB container locally:

`docker run -d --name influxdb -d -p 8086:8086 influxdb`

Start a Grafana container locally:

`docker run -d --name grafana -d -p 3000:3000 grafana/grafana`

Crete a new [python virtual environment](https://docs.python.org/3/tutorial/venv.html) and install `locust_influx`:

`pip install locust_influx`

Run the example locustfile contained in this repo (Change the host to point to desired one):

`locust -f ./locustfile.py --no-web --clients 10 --hatch-rate 1 --run-time 60s --host http://localhost:8080`

Open your local Grafana in the browser at [http://localhost:3000/](http://localhost:3000/)

Import the example dashboard from `locust_dashboard.json` file.

![Locust dashboard in grafana](https://raw.githubusercontent.com/lucrib/locust_influx/master/dashboard.png)

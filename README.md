# exchangerates2influxdb

Inspired by the great work of [aidengilmartin / speedtest-to-influxdb](https://github.com/aidengilmartin/speedtest-to-influxdb) 

Clone this repo onto your destination server and cd into the directory

```shell
cd exchangerates2influxdb/
```

Make the Python script executable

```shell
chmod +x exchangerates2influx.py
```

Create the database in InfluxDB

```shell
influx
>
> CREATE DATABASE <database name>
> CREATE USER "<username>" WITH PASSWORD '<your password>'
> GRANT ALL ON "<database name>" to "<username>"
> 
> quit
```

Make the corresponding changes at the top of the Python script:

```Python
# InfluxDB Settings
DB_ADDRESS = os.environ.get('DB_ADDRESS', '<IP addresss or localhost>')
DB_PORT = os.environ.get('DB_PORT', 8086)
DB_USER = os.environ.get('DB_USER', '<username>')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '<password>')
DB_DATABASE = os.environ.get('DB_DATABASE', '<database name>')
```

The script assumes a continuous run - and does not depend on any cron job. You need to run it in the background.

To run it in the background - and also to capture the log output in a file - execute the following:

```shell
nohup python3 -u ./exchangerates2influx.py > exchangerates-output.log &
```

To check if all is OK test if the script is actually running:

1. Check if the process has started:

```shell
ps aux | grep python3
```
You should see `python3 -u ./exchangerates2influx.py` listed.

2. Check if the exchangerates-output.log file was generated and contains some initial output:

```shell
cat exchangerates-output.log
```

You should see at least the following:

```
Info : 23/08/2021 10:20:50 : Exchangerate.host Data Logger to InfluxDB started
Info : 23/08/2021 10:20:50 : DB initialization complete
```

...and perhaps the below too:

```
Info : 23/08/2021 10:21:15 : API call to exchangerate.host successful
Info : 23/08/2021 10:21:15 : Data written to DB successfully
...
```

If all is good the last thing to check is InfluxDB that it actually contains the data captured.

```shell
influx
>
> SHOW DATABASES
...
> USE <database name>
...
> SELECT * FROM exchange_rates WHERE time > now() - 1h
...
> quit
```

You should see at least 1 entry, along the lines of:

```
name: exchange_rates
time                EUR    GBP    USD    data_source
----                ---    ---    ---    -----------
1629815226693841375 349.96 406.93 299.11 exchangerate.host
1629817042533480774 349.96 406.93 299.11 exchangerate.host
...
```

That's it.

---

Tested on a Raspberry Pi 4 Model B running Raspbian GNU/Linux 10 (buster) with
- Python 3.7.3
- InfluxDB v1.8.9 (git: 1.8 d9b56321d579)
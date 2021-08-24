import time
import os
import requests

from influxdb import InfluxDBClient
from datetime import datetime

base_currencies = ['EUR', 'USD', 'GBP']
rate_in = 'HUF'
rates = {}


# InfluxDB Settings
DB_ADDRESS = os.environ.get('DB_ADDRESS', '<IP addresss or localhost>')
DB_PORT = os.environ.get('DB_PORT', 8086)
DB_USER = os.environ.get('DB_USER', '<username>')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '<password>')
DB_DATABASE = os.environ.get('DB_DATABASE', '<database name>')
DB_RETRY_INVERVAL = int(os.environ.get('DB_RETRY_INVERVAL', 60)) # Time before retrying a failed data upload.

# API retrieval Settings
TEST_INTERVAL = int(os.environ.get('TEST_INTERVAL', 3600))  # Time between tests (in seconds).
TEST_FAIL_INTERVAL = int(os.environ.get('TEST_FAIL_INTERVAL', 60))  # Time before retrying a failed API call (in seconds).

PRINT_DATA = os.environ.get('PRINT_DATA', "False") # Do you want to see the results in your logs? Type must be str. Will be converted to bool.

influxdb_client = InfluxDBClient(
    DB_ADDRESS, DB_PORT, DB_USER, DB_PASSWORD, None)

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

def logger(level, message):
    print(level, ":", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), ":", message)

def init_db():
    try:
        databases = influxdb_client.get_list_database()
    except:
        logger("Error", "Unable to get list of databases")
        raise RuntimeError("No DB connection") from error
    else:
        if len(list(filter(lambda x: x['name'] == DB_DATABASE, databases))) == 0:
            influxdb_client.create_database(
                DB_DATABASE)  # Create if does not exist.
        else:
            influxdb_client.switch_database(DB_DATABASE)  # Switch to if does exist.


def get_rates():
    for currency in base_currencies:
        url = 'https://api.exchangerate.host/latest?base={0}&symbol={1}&places=2'.format(currency, rate_in)
        response = requests.get(url)
        exchange_rate = response.json()
        rate_in_currency = exchange_rate["rates"][rate_in]
        rates[currency] = rate_in_currency
    return rates


def format_for_influx():
    data = get_rates()
    influx_data = [
        {
            "measurement": "exchange_rates",
            "tags": {
                "data_source": "exchangerate.host"
            },
            "fields": {
                base_currencies[0]: float(data[base_currencies[0]]),
                base_currencies[1]: float(data[base_currencies[1]]),
                base_currencies[2]: float(data[base_currencies[2]])
            }
        }
    ]
    return influx_data


def main():
    db_initialized = False

    while(db_initialized == False):
        try:
            init_db()  # Setup the database if it does not already exist.
        except:
            logger("Error", "DB initialization error")
            time.sleep(int(DB_RETRY_INVERVAL))
        else:
            logger("Info", "DB initialization complete")
            db_initialized = True

    while (1):  # Run an API call and send the results to influxDB indefinitely.
        data = format_for_influx()
        logger("Info", "API call to exchangerate.host successful")
        try:
            if influxdb_client.write_points(data) == True:
                logger("Info", "Data written to DB successfully")
                if str2bool(PRINT_DATA) == True:
                    logger("Info", data)
                time.sleep(TEST_INTERVAL)
        except:
            logger("Error", "Data write to DB failed")
            time.sleep(TEST_FAIL_INTERVAL)


if __name__ == '__main__':
    logger('Info', 'Exchangerate.host Data Logger to InfluxDB started')
    main()

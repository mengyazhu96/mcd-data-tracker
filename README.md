# Crypto Data Tracker

Jessica Zhu

Monte Carlo Take-Home Assignment

This tool queries [Cryptowatch](https://docs.cryptowat.ch/rest-api/) once per
minute for
volumes and prices of cryptocurrency pairs for different markets and aggregates
data collected per pair or asset between different markets.

Some language used in this README and in the API:
- A "metric type" is either "volume" or "price."
- A "symbol" is the symbol of either a 
    [pair](https://docs.cryptowat.ch/rest-api/pairs) (e.g. "btceur") or an
    [asset](https://docs.cryptowat.ch/rest-api/assets) ("btc").
- "volume" is collected for an asset, and refers to the volume in the last
    24 hours summed across all markets.
- "price" is collected for a pair, and refers to the average price across all
    markets.

## Usage
This app uses Python 3.7.

### One-Time Setup
Install requirements:
```
pip install -r requirements.txt
```

Create the DB file and tables necessary:
```
python create_tables.py
```

### Running the Data Tracker
Start metrics collection and the web service:
```
python write_metrics.py & python api.py
```

### API Endpoints
GET `/metric_types`

Gets all tracked metric types.
```
{
    "metric_types": [
        {
            "metric_type": "price",
            "description": "Average price across all markets a symbol is traded on."
        },
        {
            "metric_type": "volume",
            "description": "Volume of a symbol in the last 24 hours, totalled over all markets."
        }
    ]
}
```

GET `/metric_types/{metric_type}`

Gets details for a given metric type.
```
{
    "metric_type": "price",
    "description": "Average price across all markets a symbol is traded on."
}
```

GET `/metric_types/{metric_type}/metrics`

Gets a list of metrics for the given metric type, identified by symbol.
```
{
    "metrics": [
        {
            "metric_type": "price",
            "symbol": "adausdt"
        },
        {
            "metric_type": "price",
            "symbol": "algousd"
        },
    ]
}
```

GET `/metric_types/{metric_type}/metrics/{symbol}`

Gets details of a metric type for a given symbol.
```
{
    "metric_type": "volume",
    "symbol": "btc"
}
```

GET `/metric_types/{metric_type}/metrics/{symbol}/history`

Gets values of specified metric for the last 24 hours.
```
{
    "history": {
        "2021-03-07T17:04:06.759915": 1458881474.9880266,
        "2021-03-07T17:05:06.769392": 1458881474.9880266,
        "2021-03-07T17:06:06.768434": 1458881474.9880266,
        "2021-03-07T17:07:06.784122": 1454029024.3984447,
        "2021-03-07T17:08:06.935114": 1454029024.3984447,
        "2021-03-07T17:09:06.721268": 1454029024.3984447,
        "2021-03-07T17:10:06.906854": 1452158558.8475633,
        // ...
    }
}
```

GET `/metric_types/{metric_type}/metrics/{symbol}/rank`

Gets the rank of the specified metric, ordered by the standard deviations
of the metric in the last 24 hours relative to other metrics of the same
`metric_type`. Ties are preserved, so a query for a metric that is
ranked last may return rank < total.
```
{
    "rank": 53,
    "total": 1050
}
```

## Architecture
There are two separate processes to this data tracker that communicate via
a database. The `write_metrics.py` script fetches upstream data, aggregates it,
and writes it to the database. The web service then only needs to read from
this database. This separation prevents potential lag caused by waiting for
the upstream data processing for users of the web service.

We use SQLite and a local file as our database for a quick startup locally. The
only table in this database is `metric_history`, and contains the following
columns:
- metric_type (string, e.g. "volume" or "price")
- symbol (string, e.g. "btc" or "btceur")
- value (float)
- timestamp (datetime)

I used Flask and Flask-RESTful for quick development of a REST API.

To productionize this, the data fetcher could exist as a
scheduled job rather than the current script that waits for a minute to pass.
In the case where we wanted to add many more metric types, we could set up one
job for each type of metric to be stored. This could also help if we wanted
sampling to happen much more frequently, as it would reduce the processing
time for each job and prevent lag for metric types that would be processed
later. We could also host the web service on a cloud server, and take
advantage of cloud service provider tools to handle load balancing in the case
of many API users.

Currently the application stores all metric history ever collected. This could
cause slow read queries in the future and also use much more database storage
than needed. We could introduce a separate process in the future to delete or
inactivate rows that are older than our window of 24 hours. For example, we
could add an "is_active" column that a separate job regularly updates for rows
that are more than 24 hours old, and
use that column for indexing to speed up the web service's DB queries.
In addition, we could add separate tables for metric type and symbol, and
introduce explicit IDs outside of symbol and metric_type for more robust
identification. We would also add
indexing on top of our DB tables for faster read queries.

I don't have experience with other database engines or database scaling, so
there may be database engines better suited to this problem than SQL / 
Postgres, and part of scaling this application could involve database
clustering.

## TODOs / Potential Improvements
There are a lot of improvements that could be made. These are some that I
thought of:
- Unit tests for DB functions
- More unit testing for `write_metrics.py`, particularly to check accuracy
    of aggregation logic
- Integration tests for API endpoints using a static DB with fake data
- Potential checks for outliers in data retrieved from upstream (e.g. one
    market's price is orders of magnitude different from the price retrieved
    from another market)
- Using a more robust DB management system like Postgres
- Error handling of responses from upstream data dependency (Cryptowatch)
- A designated API key for Cryptowatch to manage allowance limitations
- Separate code files into packages

## Feature Request
We could set up a separate alerting job that depends on the metrics 
aggregation / writing job. This job would rely on a cache
that stores the last hour of metric history for every metric type and symbol.
The metrics writing job sends the just-collected data points to this alerting
job. The alerting job then queries its cache of 1-hour history for each metric,
computes the threshold, and sends the alert if the new data point exceeds
the threshold. Whether or not an alert was sent, the alerting job throws out
the oldest cache data point and adds the new data point to its cache.

The metrics writing job does not need to wait for its request to be accepted.
It can add its request of newly collected data points to a queue for the
alerting job, so that these requests do not get processed out of order. We
could also separate the alerting job into separate jobs per metric type.

Using a separate cache duplicates the metric history stored in the existing
database table. There are a few reasons I chose to proceed with it anyways
because the metric history stored in the existing database table is never
updated, so there's no risk of existing data getting out of sync. This also
decouples the alerting job even more from the web service, as they do
not both depend on the same database. Therefore this does not impact the
availability of the web service, as the alerting job does not add query
load to the database.

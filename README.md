# Crypto Data Tracker

Jessica Zhu
Monte Carlo Take-Home Assignment

## Usage

## Design


Endpoints

GET /metric_types
{
    "metric_types": [
        {
            "metric_type": "volume"
        },
        {
            "metric_type": "price"
        }
    ]
}

GET /metric_types/{metric_type}
{
    "metric_type": "price"
}

GET /metric_types/{metric_type}/metrics
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

GET /metric_types/{metric_type}/metrics/{symbol}
{
    "metric_type": "volume",
    "symbol": "btc"
}

GET /metric_types/{metric_type}/metrics/{symbol}/history
{
    "history": [
        1.01,
        1.02,
        1.00
    ]
}

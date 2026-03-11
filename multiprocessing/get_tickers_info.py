from typing import Generator


def get_ticker(file: str) -> Generator[str, None, None]:
    with open(file) as f:
        for line in f:
            ticker = line.strip()
            yield ticker

def get_history_data(
    ticker: str, start_date: str, end_date: str, interval: str = "1d"
):
    per2 = int(
        datetime.strptime(end_date, "%d.%m.%Y").replace(tzinfo=timezone.utc).timestamp()
    )
    per1 = int(
        datetime.strptime(start_date, "%d.%m.%Y")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )

    params = {
        "period1": str(per1),
        "period2": str(per2),
        "interval": interval,
        "includeAdjustedClose": "true",
    }

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    response = requests.get(url, headers=headers, params=params, timeout=10)
    return ticker, response.json()
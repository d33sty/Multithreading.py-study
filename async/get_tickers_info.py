import asyncio
from typing import AsyncGenerator
import csv
import os
import aiohttp


async def get_ticker(file: str) -> AsyncGenerator[str, None]:
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            ticker = line.strip()
            await asyncio.sleep(0)
            yield ticker


async def get_dividends(ticker: str) -> None:
    """
    Получает дивидендные выплаты для тикера и сохраняет в CSV
    """
    url = f"http://iss.moex.com/iss/securities/{ticker}/dividends.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data: dict = await response.json()

        dividends_data: dict = data.get("dividends", {})
        columns = dividends_data.get("columns", [])
        rows = dividends_data.get("data", [])

        if not rows:
            print(f"Нет дивидендных данных для {ticker}")
            return

        # Создаем папку data если её нет
        os.makedirs("data", exist_ok=True)

        # Сохраняем в CSV
        filename = f"data/{ticker}_dividends.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # Заголовки
            writer.writerows(rows)  # Данные

        print(f"✓ Дивиденды для {ticker} сохранены ({len(rows)} записей)")

    except Exception as e:
        print(f"✗ Ошибка при получении дивидендов для {ticker}: {e}")


async def get_historical_data(
    ticker: str, from_date: str = None, till_date: str = None
) -> None:
    """
    Получает исторические данные цен для тикера и сохраняет в CSV

    Параметры:
    ticker: тикер
    from_date: дата начала в формате YYYY-MM-DD
    till_date: дата конца в формате YYYY-MM-DD
    """
    url = f"http://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"

    params = {}
    if from_date:
        params["from"] = from_date
    if till_date:
        params["till"] = till_date

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                data: dict = await response.json()

        # Извлекаем данные
        history_data = data.get("history", {})
        columns: dict = history_data.get("columns", [])
        rows: dict = history_data.get("data", [])

        if not rows:
            print(f"Нет исторических данных для {ticker}")
            return

        # Создаем папку data если её нет
        os.makedirs("data", exist_ok=True)

        # Сохраняем в CSV
        filename = f"data/{ticker}_historical.csv"
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # Заголовки
            writer.writerows(rows)  # Данные

        print(f"✓ История для {ticker} сохранена ({len(rows)} записей)")

    except Exception as e:
        print(f"✗ Ошибка при получении истории для {ticker}: {e}")


async def main():

    FROM_DATE = "2023-01-01"  # Начальная дата для исторических данных
    TILL_DATE = "2024-12-31"  # Конечная дата для исторических данных

    print(f"Период для исторических данных: {FROM_DATE} - {TILL_DATE}")

    tasks = []
    async with asyncio.TaskGroup() as tg:
        async for ticker in get_ticker("tickers.txt"):
            tasks.append(tg.create_task(get_dividends(ticker)))
            tasks.append(
                tg.create_task(get_historical_data(ticker, FROM_DATE, TILL_DATE))
            )

    print(f"\nГотово! Все данные сохранены в папке 'data'")


if __name__ == "__main__":
    asyncio.run(main())

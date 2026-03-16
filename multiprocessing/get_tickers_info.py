import requests
import csv
import os
from datetime import datetime
from typing import Generator
from concurrent.futures import ThreadPoolExecutor
import json


def get_ticker(file: str) -> Generator[str, None, None]:
    with open(file) as f:
        for line in f:
            ticker = line.strip()
            yield ticker


def get_dividends(ticker: str) -> None:
    """
    Получает дивидендные выплаты для тикера и сохраняет в CSV
    """
    url = f"http://iss.moex.com/iss/securities/{ticker}/dividends.json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Извлекаем данные
        dividends_data = data.get("dividends", {})
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


def get_historical_data(
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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Извлекаем данные
        history_data = data.get("history", {})
        columns = history_data.get("columns", [])
        rows = history_data.get("data", [])

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


def process_ticker(ticker: str, from_date: str = None, till_date: str = None) -> None:
    """
    Обрабатывает один тикер: получает дивиденды и исторические данные
    """
    print(f"\nОбработка тикера: {ticker}")
    get_dividends(ticker)
    get_historical_data(ticker, from_date, till_date)


if __name__ == "__main__":
    # Параметры запроса
    FROM_DATE = "2023-01-01"  # Начальная дата для исторических данных
    TILL_DATE = "2024-12-31"  # Конечная дата для исторических данных
    MAX_WORKERS = 5  # Количество потоков

    # Получаем список тикеров
    tickers_file = "multiprocessing/tickers.txt"
    tickers = list(get_ticker(tickers_file))

    print(f"Найдено тикеров: {len(tickers)}")
    print(f"Период для исторических данных: {FROM_DATE} - {TILL_DATE}")

    # Многопоточная обработка
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_ticker, ticker, FROM_DATE, TILL_DATE)
            for ticker in tickers
        ]

        # Ожидаем завершения всех задач
        for future in futures:
            future.result()

    print(f"\nГотово! Все данные сохранены в папке 'data'")

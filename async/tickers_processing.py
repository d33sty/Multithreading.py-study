import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import AsyncGenerator
from multiprocessing import current_process
import os
from datetime import datetime
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


async def get_ticker(file: str) -> AsyncGenerator[str, None]:
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            ticker = line.strip()
            await asyncio.sleep(0)
            yield ticker


def sync_process_ticker(ticker: str, monthly_expand: float) -> list:
    """
    Синхронная функция обработки тикера.
    Возвращает список кортежей: (дата, количество_акций, цена, общая_стоимость)
    """
    print(f"Обработка {ticker} в процессе {current_process().ident}")

    # Загружаем исторические данные
    hist_filename = f"data/{ticker}_historical.csv"
    if not os.path.exists(hist_filename):
        print(f"Файл {hist_filename} не найден")
        return []

    # Загружаем дивиденды
    div_filename = f"data/{ticker}_dividends.csv"
    dividends = {}
    if os.path.exists(div_filename):
        with open(div_filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 4:
                    date = row[2]
                    value = float(row[3])
                    dividends[date] = value

    # Читаем исторические данные
    dates = []
    closes = []

    with open(hist_filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        try:
            date_idx = headers.index("TRADEDATE")
            close_idx = headers.index("CLOSE")
        except ValueError:
            print(f"Не найдены нужные колонки в {hist_filename}")
            return []

        for row in reader:
            if len(row) > max(date_idx, close_idx):
                date = row[date_idx]
                close_str = row[close_idx]

                if not close_str or close_str.strip() == "":
                    continue

                close = float(close_str)
                dates.append(date)
                closes.append(close)

    if not dates:
        return []

    # Обрабатываем данные
    shares = 0.0
    result = []
    last_month = None

    for i, (date, price) in enumerate(zip(dates, closes)):
        current_date = datetime.strptime(date, "%Y-%m-%d")

        # Проверка на сплит (изменение цены более чем в 2 раза)
        if i > 0:
            prev_price = closes[i - 1]
            if prev_price > 0:
                ratio = prev_price / price
                # Если цена изменилась более чем в 2 раза (сплит или обратный сплит)
                if ratio >= 2.0 or ratio <= 0.5:
                    # Корректируем количество акций
                    shares = shares * ratio
                    print(
                        f"  Сплит на {ticker}: цена была {prev_price}, стала {price}, "
                        f"коэффициент {ratio:.4f}, акций стало {shares:.4f}"
                    )

        # Покупка первого числа каждого месяца
        if last_month is None or current_date.month != last_month:
            last_month = current_date.month
            if price > 0:
                shares += monthly_expand / price

        # Получение дивидендов
        if date in dividends:
            dividend_amount = shares * dividends[date]
            if price > 0 and dividend_amount > 0:
                shares += dividend_amount / price

        # Записываем результат
        total_value = shares * price
        result.append((date, round(shares, 4), price, round(total_value, 2)))

    return result


async def main() -> None:

    loop = asyncio.get_running_loop()
    num_of_tickers = 0
    async for _ in get_ticker("tickers.txt"):
        num_of_tickers += 1

    MONTHLY_EXPAND = 10000
    MONTHLY_EXPAND_FOR_TICKER = round(MONTHLY_EXPAND / num_of_tickers, 2)

    with ProcessPoolExecutor() as executor:
        async with asyncio.TaskGroup() as tg:
            tasks = {}
            async for ticker in get_ticker("tickers.txt"):
                tasks[ticker] = loop.run_in_executor(
                    executor, sync_process_ticker, ticker, MONTHLY_EXPAND_FOR_TICKER
                )

    results = {}
    async for ticker in get_ticker("tickers.txt"):
        result = await tasks[ticker]
        results[ticker] = result

    # Сбор всех дат и расчёт вклада
    all_dates = set()
    for data in results.values():
        for row in data:
            all_dates.add(row[0])

    sorted_dates = sorted(all_dates)

    deposit = 0.0
    deposit_values = []
    annual_rate = 0.07
    monthly_rate = annual_rate / 12
    last_month = None

    for date in sorted_dates:
        current_date = datetime.strptime(date, "%Y-%m-%d")

        # Начисляем проценты за прошедший месяц
        if last_month is not None and current_date.month != last_month:
            deposit *= 1 + monthly_rate

        # Пополняем в первое число месяца
        if last_month is None or current_date.month != last_month:
            deposit += MONTHLY_EXPAND

        last_month = current_date.month
        deposit_values.append(deposit)

    # Расчёт общей стоимости портфеля по всем тикерам на каждую дату
    portfolio_total_by_date = {}
    for ticker, data in results.items():
        for row in data:
            date = row[0]
            total_value = row[3]
            if date not in portfolio_total_by_date:
                portfolio_total_by_date[date] = 0.0
            portfolio_total_by_date[date] += total_value

    # Построение графиков
    plt.figure(figsize=(14, 8))

    # Графики акций (каждый тикер отдельно)
    for ticker, data in results.items():
        if not data:
            continue

        dates = [datetime.strptime(row[0], "%Y-%m-%d") for row in data]
        total_values = [row[3] for row in data]
        plt.plot(dates, total_values, label=ticker, linewidth=1.5, alpha=0.7)

    # График общего портфеля по всем тикерам
    portfolio_dates = [
        datetime.strptime(d, "%Y-%m-%d") for d in portfolio_total_by_date.keys()
    ]
    portfolio_values = list(portfolio_total_by_date.values())
    plt.plot(
        portfolio_dates,
        portfolio_values,
        label="Общий портфель (все тикеры)",
        linewidth=2,
        color="green",
        linestyle="-",
    )

    # График вклада
    deposit_dates = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
    plt.plot(
        deposit_dates,
        deposit_values,
        label=f"Банковский вклад ({round(annual_rate*100, 0)}% годовых)",
        linewidth=2,
        color="red",
    )

    plt.xlabel("Дата")
    plt.ylabel("Стоимость (руб)")
    plt.title("Динамика стоимости портфеля по акциям vs банковский вклад")
    plt.legend(loc="best", fontsize=8)
    plt.grid(True, alpha=0.3)

    # Настройка подписей оси дат
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator())

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("portfolio_dynamics.png", dpi=150)

    # Вывод финальных результатов
    print("\n" + "=" * 60)
    print("Финальная стоимость портфеля по каждому тикеру:")
    print("=" * 60)

    total_portfolio_value = 0
    for ticker, data in results.items():
        if data:
            last_date, shares, price, total_value = data[-1]
            total_portfolio_value += total_value
            print(
                f"{ticker}: {total_value:,.2f} руб (акций: {shares:.4f}, цена: {price:.2f})"
            )
        else:
            print(f"{ticker}: Нет данных")

    print("=" * 60)
    print(f"ИТОГО ПОРТФЕЛЬ: {total_portfolio_value:,.2f} руб")
    print(f"БАНКОВСКИЙ ВКЛАД: {deposit:,.2f} руб")
    print(
        f"РАЗНИЦА: {total_portfolio_value - deposit:+,.2f} руб, {-(1-total_portfolio_value/deposit)*100:+,.2f} %"
    )
    print("=" * 60)

    plt.show()


if __name__ == "__main__":
    asyncio.run(main())

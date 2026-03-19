import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from functools import partial


def ensure_results_folder():
    """Создает папку results если её нет"""
    os.makedirs("results", exist_ok=True)
    return "results"


def load_dividends(ticker):
    """Загружает дивидендные выплаты для тикера"""
    filename = f"data/{ticker}_dividends.csv"
    if not os.path.exists(filename):
        return pd.DataFrame()

    df = pd.read_csv(filename)
    if "registryclosedate" not in df.columns:
        return pd.DataFrame()

    df["registryclosedate"] = pd.to_datetime(df["registryclosedate"])
    # Добавляем 8 торговых дней для получения дивидендов
    df["payment_date"] = df["registryclosedate"] + pd.Timedelta(
        days=12
    )  # ~8 торговых дней
    return df[["registryclosedate", "payment_date", "value"]].rename(
        columns={"value": "dividend", "registryclosedate": "ex_date"}
    )


def load_historical(ticker):
    """Загружает исторические данные для тикера"""
    filename = f"data/{ticker}_historical.csv"
    if not os.path.exists(filename):
        return pd.DataFrame()

    df = pd.read_csv(filename)
    df["TRADEDATE"] = pd.to_datetime(df["TRADEDATE"])
    df = df.sort_values("TRADEDATE")
    return df[["TRADEDATE", "CLOSE", "SECID"]].rename(
        columns={"TRADEDATE": "date", "CLOSE": "price", "SECID": "ticker"}
    )


def load_ticker_data(ticker):
    """Загружает данные для одного тикера (для параллельной загрузки)"""
    hist = load_historical(ticker)
    divs = load_dividends(ticker)
    return ticker, hist, divs


def calculate_ticker_returns(ticker_data, price_history):
    """
    Рассчитывает дневную доходность для одного тикера с учетом дивидендов
    """
    ticker, hist, divs = ticker_data

    if hist.empty:
        return ticker, pd.DataFrame()

    # Создаем ежедневный ряд цен
    all_dates = price_history.index
    ticker_prices = hist.set_index("date")["price"].reindex(all_dates).ffill()

    # Рассчитываем дневную доходность без дивидендов
    daily_returns = ticker_prices.pct_change().fillna(0)

    # Добавляем дивидендную доходность
    if not divs.empty:
        for _, div in divs.iterrows():
            payment_date = div["payment_date"]
            if payment_date in ticker_prices.index:
                price_before = ticker_prices.loc[payment_date]
                if price_before > 0:
                    dividend_yield = div["dividend"] / price_before
                    daily_returns.loc[payment_date] += dividend_yield

    return ticker, daily_returns


def parallel_data_loading(tickers, max_workers=None):
    """
    Параллельная загрузка данных для всех тикеров
    """
    if max_workers is None:
        max_workers = min(len(tickers), multiprocessing.cpu_count())

    print(f"Загрузка данных для {len(tickers)} тикеров с {max_workers} процессами...")

    ticker_data_dict = {}
    hist_data_list = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(load_ticker_data, ticker): ticker for ticker in tickers
        }

        for future in as_completed(futures):
            ticker, hist, divs = future.result()
            ticker_data_dict[ticker] = (hist, divs)
            if not hist.empty:
                hist_data_list.append(hist)
            print(f"✓ Загружен {ticker}")

    return ticker_data_dict, (
        pd.concat(hist_data_list) if hist_data_list else pd.DataFrame()
    )


def parallel_returns_calculation(ticker_data_dict, price_history, max_workers=None):
    """
    Параллельный расчет доходностей для всех тикеров
    """
    if max_workers is None:
        max_workers = min(len(ticker_data_dict), multiprocessing.cpu_count())

    print(
        f"\nРасчет доходностей для {len(ticker_data_dict)} тикеров с {max_workers} процессами..."
    )

    returns_dict = {}

    # Подготавливаем данные для передачи в процессы
    items = []
    for ticker, (hist, divs) in ticker_data_dict.items():
        items.append((ticker, hist, divs))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        calc_func = partial(calculate_ticker_returns, price_history=price_history)
        futures = {executor.submit(calc_func, item): item[0] for item in items}

        for future in as_completed(futures):
            ticker, returns = future.result()
            if not returns.empty:
                returns_dict[ticker] = returns
            print(f"✓ Рассчитан {ticker}")

    return returns_dict


def calculate_portfolio_parallel(
    tickers, start_date="2023-01-01", monthly_investment=10000
):
    """
    Рассчитывает портфель с использованием многопроцессности
    """
    results_folder = ensure_results_folder()

    # Параллельная загрузка данных
    ticker_data_dict, all_hist = parallel_data_loading(tickers)

    if all_hist.empty:
        print("Нет данных для расчета")
        return pd.DataFrame(), pd.DataFrame(), []

    # Создаем полный календарь дат
    all_dates = pd.date_range(start=start_date, end=all_hist["date"].max(), freq="D")
    price_history = pd.DataFrame(index=all_dates)

    # Параллельный расчет доходностей
    returns_dict = parallel_returns_calculation(ticker_data_dict, price_history)

    # Собираем цены для всех тикеров
    portfolio_pivot = pd.DataFrame(index=all_dates)
    for ticker, (hist, _) in ticker_data_dict.items():
        if not hist.empty:
            prices = hist.set_index("date")["price"].reindex(all_dates).ffill()
            portfolio_pivot[ticker] = prices

    # Расчет портфеля в деньгах
    cash_flow = []
    result = []

    shares = {ticker: 0.0 for ticker in portfolio_pivot.columns}
    total_invested = 0
    last_month = None

    # Загружаем все дивиденды для быстрого доступа
    all_dividends = []
    for ticker, (_, divs) in ticker_data_dict.items():
        if not divs.empty:
            divs["ticker"] = ticker
            all_dividends.append(divs)

    dividends_df = pd.concat(all_dividends) if all_dividends else pd.DataFrame()

    for date in all_dates:
        current_prices = portfolio_pivot.loc[date]
        current_value = sum(
            shares[t] * current_prices[t]
            for t in shares.keys()
            if not pd.isna(current_prices[t])
        )

        # Ежемесячная покупка 31 числа
        if date.day == 31 and (last_month is None or date.month != last_month):
            last_month = date.month
            invest_per_ticker = monthly_investment / len(shares)

            for ticker in shares.keys():
                price = current_prices[ticker]
                if not pd.isna(price) and price > 0:
                    shares[ticker] += invest_per_ticker / price
                    total_invested += invest_per_ticker
                    cash_flow.append(
                        {
                            "date": date,
                            "amount": invest_per_ticker,
                            "type": "investment",
                        }
                    )

        # Получение дивидендов
        if not dividends_df.empty:
            day_dividends = dividends_df[dividends_df["payment_date"] == date]
            for _, div in day_dividends.iterrows():
                ticker = div["ticker"]
                if ticker in shares and shares[ticker] > 0:
                    dividend_amount = shares[ticker] * div["dividend"]

                    # Реинвестируем дивиденды
                    price = current_prices[ticker]
                    if not pd.isna(price) and price > 0:
                        shares[ticker] += dividend_amount / price
                        cash_flow.append(
                            {
                                "date": date,
                                "amount": dividend_amount,
                                "type": "dividend",
                            }
                        )

        # Записываем результат
        result.append(
            {
                "date": date,
                "portfolio_value": current_value,
                "total_invested": total_invested,
                "profit": current_value - total_invested,
                "profit_percent": (
                    (current_value / total_invested - 1) * 100
                    if total_invested > 0
                    else 0
                ),
                **{f"shares_{t}": shares[t] for t in shares.keys()},
            }
        )

    result_df = pd.DataFrame(result)
    cash_flow_df = pd.DataFrame(cash_flow) if cash_flow else pd.DataFrame()

    return result_df, cash_flow_df, portfolio_pivot.columns.tolist()


def plot_portfolio(result_df, cash_flow_df, tickers):
    """Строит график портфеля и сохраняет в папку results"""
    results_folder = ensure_results_folder()

    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=(
            "Динамика портфеля",
            "Ежемесячные пополнения и дивиденды",
            "Распределение акций",
        ),
        vertical_spacing=0.1,
        row_heights=[0.5, 0.25, 0.25],
    )

    # График портфеля
    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["portfolio_value"],
            name="Стоимость портфеля",
            line=dict(color="blue", width=2),
            hovertemplate="Дата: %{x}<br>Стоимость: %{y:,.0f} ₽<extra></extra>",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["total_invested"],
            name="Вложено всего",
            line=dict(color="green", width=2, dash="dash"),
            hovertemplate="Дата: %{x}<br>Вложено: %{y:,.0f} ₽<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Прибыль/убыток
    colors = ["red" if x < 0 else "green" for x in result_df["profit"]]
    fig.add_trace(
        go.Bar(
            x=result_df["date"],
            y=result_df["profit"],
            name="Прибыль/убыток",
            marker_color=colors,
            hovertemplate="Дата: %{x}<br>Прибыль: %{y:,.0f} ₽<extra></extra>",
        ),
        row=2,
        col=1,
    )

    # Распределение акций
    for ticker in tickers:
        if f"shares_{ticker}" in result_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=result_df["date"],
                    y=result_df[f"shares_{ticker}"],
                    name=ticker,
                    stackgroup="one",
                    hovertemplate=f"{ticker}: %{{y:.2f}} шт<extra></extra>",
                ),
                row=3,
                col=1,
            )

    fig.update_layout(
        title="Портфель долгосрочного инвестора (многопроцессный расчет)",
        hovermode="x unified",
        height=900,
        showlegend=True,
    )

    fig.update_xaxes(title_text="Дата", row=3, col=1)
    fig.update_yaxes(title_text="Рубли", row=1, col=1)
    fig.update_yaxes(title_text="Прибыль (₽)", row=2, col=1)
    fig.update_yaxes(title_text="Количество акций", row=3, col=1)

    # Сохраняем в папку results
    fig.write_html(os.path.join(results_folder, "portfolio_result_parallel.html"))
    print(f"График сохранен в {results_folder}/portfolio_result_parallel.html")

    # Показываем график (опционально, можно закомментировать если не нужно)
    fig.show()


def print_statistics(result_df, cash_flow_df, tickers):
    """Выводит статистику портфеля"""
    if result_df.empty:
        return

    last_row = result_df.iloc[-1]

    print("\n" + "=" * 60)
    print("СТАТИСТИКА ПОРТФЕЛЯ (многопроцессный расчет)")
    print("=" * 60)
    print(f"Дата последней оценки: {last_row['date'].strftime('%Y-%m-%d')}")
    print(f"Всего вложено: {last_row['total_invested']:,.0f} ₽")
    print(f"Текущая стоимость: {last_row['portfolio_value']:,.0f} ₽")
    print(f"Прибыль: {last_row['profit']:+,.0f} ₽ ({last_row['profit_percent']:+.1f}%)")

    print("\n" + "-" * 60)
    print("АКТИВЫ")
    print("-" * 60)
    for ticker in tickers:
        shares_col = f"shares_{ticker}"
        if shares_col in result_df.columns:
            shares = last_row[shares_col]
            if shares > 0:
                print(f"{ticker}: {shares:.2f} шт")

    if not cash_flow_df.empty:
        total_investments = cash_flow_df[cash_flow_df["type"] == "investment"][
            "amount"
        ].sum()
        total_dividends = cash_flow_df[cash_flow_df["type"] == "dividend"][
            "amount"
        ].sum()
        print(f"\nВсего инвестиций: {total_investments:,.0f} ₽")
        print(f"Всего дивидендов: {total_dividends:,.0f} ₽")

    print("=" * 60)


def save_results_to_folder(result_df, cash_flow_df):
    """Сохраняет CSV файлы в папку results"""
    results_folder = ensure_results_folder()

    # Сохраняем детальные результаты
    result_df.to_csv(
        os.path.join(results_folder, "portfolio_detailed_parallel.csv"), index=False
    )
    print(
        f"Детальные результаты сохранены в {results_folder}/portfolio_detailed_parallel.csv"
    )

    # Сохраняем денежные потоки
    if not cash_flow_df.empty:
        cash_flow_df.to_csv(
            os.path.join(results_folder, "cash_flow_parallel.csv"), index=False
        )
        print(f"Денежные потоки сохранены в {results_folder}/cash_flow_parallel.csv")


if __name__ == "__main__":
    # Создаем папку для результатов
    ensure_results_folder()

    # Выбираем компании из разных секторов
    tickers = [
        "SBER",  # Банковский сектор
        "LKOH",  # Нефтегазовый сектор
        "GMKN",  # Металлургия
        "YNDX",  # IT сектор
        "PHOR",  # Химия/Удобрения
    ]

    print(f"Многопроцессный анализ портфеля из {len(tickers)} компаний:")
    for t in tickers:
        print(f"  - {t}")

    # Засекаем время выполнения
    import time

    start_time = time.time()

    # Рассчитываем портфель с многопроцессностью
    result_df, cash_flow_df, available_tickers = calculate_portfolio_parallel(
        tickers=tickers, start_date="2023-01-01", monthly_investment=10000
    )

    execution_time = time.time() - start_time
    print(f"\nВремя выполнения: {execution_time:.2f} секунд")

    if result_df.empty:
        print("Не удалось рассчитать портфель. Проверьте наличие данных в папке data/")
    else:
        # Выводим статистику
        print_statistics(result_df, cash_flow_df, available_tickers)

        # Строим график (сохраняется в results)
        plot_portfolio(result_df, cash_flow_df, available_tickers)

        # Сохраняем CSV в results
        save_results_to_folder(result_df, cash_flow_df)

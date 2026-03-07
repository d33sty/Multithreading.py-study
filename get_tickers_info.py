import requests
from datetime import datetime, timezone
from typing import Generator
from concurrent.futures import ThreadPoolExecutor
import os
import csv


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


def process_ticker_data(ticker, data):
    """Обрабатывает данные для одного тикера и сохраняет в CSV"""
    try:
        os.makedirs("data", exist_ok=True)
        
        result = data.get("chart", {}).get("result", [{}])[0]
        timestamps = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        adjclose_data = result.get("indicators", {}).get("adjclose", [{}])[0]
        
        if not timestamps or not quote:
            print(f"Нет данных для {ticker}")
            return None
        
        # Получаем значения adjclose
        adjclose_values = []
        if adjclose_data and "adjclose" in adjclose_data:
            adjclose_values = adjclose_data.get("adjclose", [])
        else:
            # Если нет adjclose, используем close
            adjclose_values = quote.get("close", [])
        
        if not adjclose_values:
            print(f"Нет данных для нормализации для {ticker}")
            return None
        
        # Базовое значение для нормализации (первый adjclose)
        base_adjclose = adjclose_values[0]
        
        headers = ["datetime"] + list(quote.keys())
        if adjclose_data and "adjclose" in adjclose_data:
            headers.append("adjclose")
        headers.append("normalized")
        
        filename = f"data/{ticker}.csv"
        last_normalized = None
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for i, timestamp in enumerate(timestamps):
                dt = datetime.fromtimestamp(timestamp)
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                
                row = [dt_str]
                
                for key in quote.keys():
                    values = quote.get(key, [])
                    row.append(values[i] if i < len(values) else None)
                
                if adjclose_data and "adjclose" in adjclose_data:
                    adj_values = adjclose_data.get("adjclose", [])
                    adj_value = adj_values[i] if i < len(adj_values) else None
                    row.append(adj_value)
                    
                    if adj_value is not None and base_adjclose != 0:
                        normalized = 100 * (adj_value / base_adjclose)
                        row.append(round(normalized, 2))
                        if i == len(timestamps) - 1:  # последняя запись
                            last_normalized = round(normalized, 2)
                    else:
                        row.append(None)
                else:
                    close_values = quote.get("close", [])
                    close_value = close_values[i] if i < len(close_values) else None
                    
                    if close_value is not None and base_adjclose != 0:
                        normalized = 100 * (close_value / base_adjclose)
                        row.append(round(normalized, 2))
                        if i == len(timestamps) - 1:
                            last_normalized = round(normalized, 2)
                    else:
                        row.append(None)
                
                writer.writerow(row)
        
        print(f"✓ {ticker}")
        return last_normalized
        
    except Exception as e:
        print(f"✗ {ticker}: {e}")
        return None


user_agent_key = "User-Agent"
user_agent_value = "Mozilla/5.0"
headers = {user_agent_key: user_agent_value}

tickers_file = "data/tickers.txt"


if __name__ == "__main__":
    tickers = list(get_ticker(tickers_file))
    
    with ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(get_history_data, ticker, "01.01.2020", "07.03.2026")
            for ticker in tickers
        ]
        
        # Словарь для хранения последних normalized значений
        growth_data = {}
        
        for future in futures:
            ticker, data = future.result()
            last_normalized = process_ticker_data(ticker, data)
            if last_normalized is not None:
                growth_data[ticker] = last_normalized
    
    print(f"\nГотово! Обработано {len(tickers)} тикеров")
    
    # Вывод топа тикеров по росту
    if growth_data:
        print("\n" + "="*60)
        print("ТОП ТИКЕРОВ ПО РОСТУ (normalized):")
        print("="*60)
        
        # Сортируем по убыванию normalized
        sorted_growth = sorted(growth_data.items(), key=lambda x: x[1], reverse=True)
        
        # Выводим топ-10 или все, если меньше 10
        print(f"{'№':<4} {'Тикер':<10} {'Рост %':>12} {'Изменение %':>15}")
        print("-"*60)
        
        for i, (ticker, value) in enumerate(sorted_growth[:10], 1):
            change = value - 100
            print(f"{i:<4} {ticker:<10} {value:>10.2f}% {change:>+14.2f}%")
        
        print("="*60)
        
        # Дополнительная статистика
        if len(sorted_growth) > 10:
            print(f"\nВсего проанализировано тикеров: {len(sorted_growth)}")
        
        # Находим лучший и худший
        best = sorted_growth[0]
        worst = sorted_growth[-1]
        
        print(f"\n📈 Лучший рост: {best[0]} ({best[1]:.2f}%, {best[1]-100:+.2f}%)")
        print(f"📉 Худший рост: {worst[0]} ({worst[1]:.2f}%, {worst[1]-100:+.2f}%)")
        
        # Средний рост
        avg_growth = sum(value for _, value in sorted_growth) / len(sorted_growth)
        print(f"📊 Средний рост: {avg_growth:.2f}% ({avg_growth-100:+.2f}%)")
        
        # Медианный рост
        median_growth = sorted_growth[len(sorted_growth)//2][1]
        print(f"📊 Медианный рост: {median_growth:.2f}% ({median_growth-100:+.2f}%)")
    else:
        print("\nНет данных для анализа роста")
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os


def plot_normalized_data(data_folder="data"):
    """Строит графики normalized от datetime для всех тикеров"""
    
    # Создаем фигуру
    fig = go.Figure()
    
    # Получаем список всех CSV файлов
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]
    
    if not csv_files:
        print("Нет CSV файлов для построения графиков")
        return
    
    # Для каждого файла добавляем линию на график
    for csv_file in csv_files:
        try:
            # Читаем CSV файл
            filepath = os.path.join(data_folder, csv_file)
            df = pd.read_csv(filepath)
            
            # Получаем имя тикера (без расширения .csv)
            ticker = csv_file.replace('.csv', '')
            
            # Преобразуем datetime в формат datetime
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            # Сортируем по дате (на всякий случай)
            df = df.sort_values('datetime')
            
            # Добавляем линию на график
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df['normalized'],
                mode='lines',
                name=ticker,
                line=dict(width=1.5),
                hovertemplate=f'{ticker}<br>Date: %{{x}}<br>Normalized: %{{y:.2f}}<extra></extra>'
            ))
            
        except Exception as e:
            print(f"Ошибка при обработке {csv_file}: {e}")
    
    # Настраиваем layout
    fig.update_layout(
        title='Нормализованные цены акций (базовое значение = 100)',
        xaxis_title='Дата',
        yaxis_title='Нормализованная цена',
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        template='plotly_white',
        width=1200,
        height=700
    )
    
    # Добавляем сетку
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    # Показываем график
    fig.show()
    
    # Сохраняем в HTML файл (опционально)
    fig.write_html("normalized_prices.html")
    print("График сохранен в файл normalized_prices.html")


if __name__ == "__main__":
    # Этот код должен выполняться ПОСЛЕ сбора всех данных
    plot_normalized_data()
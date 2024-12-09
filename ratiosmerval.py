import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import requests
from datetime import datetime
import time

# Predefined tickers list
tickers = [
  "GGAL.BA", "YPFD.BA", "PAMP.BA", "TXAR.BA", "ALUA.BA", "CRES.BA", "SUPV.BA", "CEPU.BA", "BMA.BA",
  "TGSU2.BA", "TRAN.BA", "EDN.BA", "LOMA.BA", "MIRG.BA", "DGCU2.BA", "BBAR.BA", "MOLI.BA", "TGNO4.BA",
  "CGPA2.BA", "COME.BA", "IRSA.BA", "BYMA.BA", "TECO2.BA", "METR.BA", "CECO2.BA", "BHIP.BA", "AGRO.BA",
  "LEDE.BA", "CVH.BA", "HAVA.BA", "AUSO.BA", "VALO.BA", "SEMI.BA", "INVJ.BA", "CTIO.BA", "MORI.BA",
  "HARG.BA", "GCLA.BA", "SAMI.BA", "BOLT.BA", "MOLA.BA", "CAPX.BA", "OEST.BA", "LONG.BA", "GCDI.BA",
  "GBAN.BA", "CELU.BA", "FERR.BA", "CADO.BA", "GAMI.BA", "PATA.BA", "CARC.BA", "BPAT.BA", "RICH.BA",
  "INTR.BA", "GARO.BA", "FIPL.BA", "GRIM.BA", "DYCA.BA", "POLL.BA", "DOME.BA", "ROSE.BA", "MTR.BA"
]

# Helper function to find the most recent valid trading date
def get_recent_valid_date(start_date, end_date):
  while end_date.weekday() >= 5:  # Skip weekends
      end_date -= pd.Timedelta(days=1)
  return end_date

# Streamlit UI
st.title('Análisis de Ratios de Activos del MERVAL. De MTAURUS - X: https://x.com/MTaurus_ok')

# Sidebar inputs
# Add this in the sidebar section
with st.sidebar:
  data_source = st.radio(
      "Fuente de datos:",
      ('YFinance', 'AnálisisTécnico.com.ar', 'IOL (Invertir Online)', 'ByMA Data')
  )

with st.sidebar:
  main_stock_input = st.text_input('Ingresar manualmente un ticker principal (si no está en la lista):', '').upper()
  main_stock = st.selectbox(
      'Seleccionar el ticker principal:',
      options=[main_stock_input] + tickers if main_stock_input else tickers,
      index=0 if main_stock_input else 0
  )

  extra_stocks_input = st.text_input('Ingresar manualmente tickers adicionales (separados por comas):', '').upper()
  extra_stocks_manual = [ticker.strip() for ticker in extra_stocks_input.split(',') if ticker.strip()]
  extra_stocks_options = list(set(extra_stocks_manual + tickers))
  extra_stocks = st.multiselect(
      'Seleccionar hasta 6 tickers adicionales:',
      options=extra_stocks_options,
      default=extra_stocks_manual[:6]
  )
  show_filled_area = st.checkbox('Mostrar área coloreada entre líneas de desviación estándar', value=True)
  max_start_date = pd.to_datetime("2024-09-30")
  start_date = st.date_input("Fecha de inicio", pd.to_datetime("1980-01-01"), max_value=max_start_date)
  end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"), min_value=start_date)

  start_date = pd.Timestamp(start_date).normalize()
  end_date = pd.Timestamp(end_date).normalize()

  today = pd.Timestamp("today").normalize()
  most_recent_valid_date = get_recent_valid_date(start_date, today)
  reference_date = st.date_input("Fecha de referencia para visualizar como porcentajes:", most_recent_valid_date)
  reference_date = pd.Timestamp(reference_date).normalize()

  view_as_percentages = st.checkbox('Ver como porcentajes en vez de ratios')
  sma_period = st.number_input('Periodo de SMA', min_value=1, value=20, key='sma_period')
  calculation_method = st.selectbox(
      'Seleccionar método de cálculo:',
      options=['Precio Ratio', 'Precio * Volumen Ratio']
  )


  if view_as_percentages:
      st.info("La escala logarítmica está deshabilitada cuando se visualizan los datos como porcentajes.")
      use_log_scale = False
  else:
      use_log_scale = st.checkbox('Usar escala logarítmica para el eje Y', value=False)
# Add this in the sidebar section with other checkboxes
with st.sidebar:
  normalize_by_ccl = st.checkbox('Normalizar precios por CCL', value=False)

# Add these functions before the main code
def fetch_data_analisistecnico(ticker, start_date, end_date):
  try:
      from_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
      to_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())

      cookies = {
          'ChyrpSession': '0e2b2109d60de6da45154b542afb5768',
          'i18next': 'es',
          'PHPSESSID': '5b8da4e0d96ab5149f4973232931f033',
      }

      headers = {
          'accept': '*/*',
          'content-type': 'text/plain',
          'referer': 'https://analisistecnico.com.ar/',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      }

      params = {
          'symbol': ticker.replace('.BA', ''),
          'resolution': 'D',
          'from': str(from_timestamp),
          'to': str(to_timestamp),
      }

      response = requests.get(
          'https://analisistecnico.com.ar/services/datafeed/history',
          params=params,
          cookies=cookies,
          headers=headers,
      )

      if response.status_code == 200:
          data = response.json()
          df = pd.DataFrame({
              'Date': pd.to_datetime(data['t'], unit='s'),
              'Adj Close': data['c'],
              'Volume': data['v']
          })
          # Remove duplicates before setting index
          df = df.drop_duplicates(subset=['Date'])
          df = df.set_index('Date')
          return df
      return pd.DataFrame()
  except Exception as e:
      st.warning(f"Error fetching data from AnálisisTécnico for {ticker}: {e}")
      return pd.DataFrame()


def fetch_data_iol(ticker, start_date, end_date):
  try:
      from_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
      to_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())

      cookies = {
          'intencionApertura': '0',
          '__RequestVerificationToken': 'DTGdEz0miQYq1kY8y4XItWgHI9HrWQwXms6xnwndhugh0_zJxYQvnLiJxNk4b14NmVEmYGhdfSCCh8wuR0ZhVQ-oJzo1',
          'isLogged': '1',
          'uid': '1107644',
      }

      headers = {
          'accept': '*/*',
          'content-type': 'text/plain',
          'referer': 'https://iol.invertironline.com/titulo/cotizacion/BCBA/',
          'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      }

      params = {
          'symbolName': ticker.replace('.BA', ''),
          'exchange': 'BCBA',
          'from': str(from_timestamp),
          'to': str(to_timestamp),
          'resolution': 'D',
      }

      response = requests.get(
          'https://iol.invertironline.com/api/cotizaciones/history',
          params=params,
          cookies=cookies,
          headers=headers,
      )

      if response.status_code == 200:
          data = response.json()
          if data.get('status') == 'ok' and 'bars' in data:
              # Convert the bars data to a DataFrame
              df = pd.DataFrame(data['bars'])

              # Convert timestamp to datetime
              df['Date'] = pd.to_datetime(df['time'], unit='s').dt.normalize()
              df = df.drop('time', axis=1)

              # Handle duplicate dates before setting index
              df = df.groupby('Date', as_index=False).agg({
                  'close': 'last',
                  'volume': 'sum'
              })

              # Rename columns
              df = df.rename(columns={
                  'close': 'Adj Close',
                  'volume': 'Volume'
              })

              # Set index
              df = df.set_index('Date')

              # Sort index
              df = df.sort_index()

              # Convert to numeric values
              df['Adj Close'] = pd.to_numeric(df['Adj Close'], errors='coerce')
              df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')

              # Create a complete date range
              full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
              df = df.reindex(full_idx)

              # Forward fill missing values
              df = df.fillna(method='ffill')

              # Debug information
              st.write(f"Debug - Final processed data for {ticker}:")
              st.write(f"Shape: {df.shape}")
              st.write(f"Date range: {df.index.min()} to {df.index.max()}")
              st.write(f"Sample data:")
              st.write(df.head())
              st.write(f"Data types:")
              st.write(df.dtypes)

              return df

      return pd.DataFrame()

  except Exception as e:
      st.warning(f"Error fetching data from IOL for {ticker}: {str(e)}")
      import traceback
      st.write("Full error:", traceback.format_exc())
      return pd.DataFrame()

def fetch_data_byma(ticker, start_date, end_date):
  try:
      from_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
      to_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())

      cookies = {
          'JSESSIONID': '5080400C87813D22F6CAF0D3F2D70338',
          '_fbp': 'fb.2.1728347943669.954945632708052302',
      }

      headers = {
          'Accept': 'application/json, text/plain, */*',
          'Accept-Language': 'de-DE,de;q=0.9,es-AR;q=0.8,es;q=0.7,en-DE;q=0.6,en;q=0.5,en-US;q=0.4',
          'Connection': 'keep-alive',
          'DNT': '1',
          'Referer': 'https://open.bymadata.com.ar/',
          'Sec-Fetch-Dest': 'empty',
          'Sec-Fetch-Mode': 'cors',
          'Sec-Fetch-Site': 'same-origin',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
          'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"Windows"',
      }

      # Remove .BA suffix and add 24HS
      symbol = ticker.replace('.BA', '') + ' 24HS'

      params = {
          'symbol': symbol,
          'resolution': 'D',
          'from': str(from_timestamp),
          'to': str(to_timestamp),
      }

      # Disable SSL verification
      import urllib3
      urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

      response = requests.get(
          'https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/chart/historical-series/history',
          params=params,
          cookies=cookies,
          headers=headers,
          verify=False
      )

      if response.status_code == 200:
          data = response.json()
          if data.get('s') != 'ok':
              st.warning(f"Error in API response for {ticker}: {data.get('s')}")
              return pd.DataFrame()

          df = pd.DataFrame({
              'Date': pd.to_datetime(data['t'], unit='s'),
              'Adj Close': data['c'],
              'Volume': data['v']
          })

          df = df.drop_duplicates(subset=['Date'])
          df = df.set_index('Date')
          return df

      return pd.DataFrame()
  except Exception as e:
      st.warning(f"Error fetching data from ByMA Data for {ticker}: {e}")
      return pd.DataFrame()

# Create a unified data fetching function
def fetch_data(ticker, start_date, end_date, source):
  if source == 'YFinance':
      data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
      return data[['Adj Close', 'Volume']]
  elif source == 'AnálisisTécnico.com.ar':
      return fetch_data_analisistecnico(ticker, start_date, end_date)
  elif source == 'IOL (Invertir Online)':
      return fetch_data_iol(ticker, start_date, end_date)
  elif source == 'ByMA Data':
      return fetch_data_byma(ticker, start_date, end_date)
  return pd.DataFrame()
# Add this function to create consistent watermarks
def add_watermark(fig):
  fig.add_annotation(
      text="MTaurus - X: @MTaurus_ok",
      xref="paper", yref="paper",
      x=0.5, y=0.5,
      showarrow=False,
      font=dict(size=30, color="rgba(150,150,150,0.3)"),
      textangle=-30,
      opacity=0.3
  )
# Fetch and process data
# Replace the yf.download section with this:
# Replace the entire data fetching section with this:
# In the main button click handler:
# Add this function to get CCL ratio based on data source
def get_ccl_ratio(data_source, start_date, end_date):
  if data_source == 'YFinance':
      # Get YPFD.BA and YPF data
      ypfd = fetch_data('YPFD.BA', start_date, end_date, data_source)
      ypf = fetch_data('YPF', start_date, end_date, data_source)

      if not ypfd.empty and not ypf.empty:
          # Convert indexes to timezone-naive if they're tz-aware
          if ypfd.index.tz is not None:
              ypfd.index = ypfd.index.tz_localize(None)
          if ypf.index.tz is not None:
              ypf.index = ypf.index.tz_localize(None)

          # Create a complete date range
          full_index = pd.date_range(start=min(ypfd.index.min(), ypf.index.min()),
                                   end=max(ypfd.index.max(), ypf.index.max()),
                                   freq='D')

          # Reindex and forward fill
          ypfd = ypfd.reindex(full_index).ffill()
          ypf = ypf.reindex(full_index).ffill()

          ccl = ypfd['Adj Close'] / ypf['Adj Close']
          return ccl
      else:
          st.warning("No se pudo obtener CCL usando YPFD/YPF")
          return None

  elif data_source == 'IOL (Invertir Online)':
      # Get AL30 and AL30C data
      al30 = fetch_data('AL30', start_date, end_date, data_source)
      al30c = fetch_data('AL30C', start_date, end_date, data_source)

      if not al30.empty and not al30c.empty:
          ccl = al30['Adj Close'] / al30c['Adj Close']
      else:
          st.warning("No se pudo obtener CCL usando AL30/AL30C")
          return None

  elif data_source == 'ByMA Data':
      # Get AL30 and AL30C data
      al30 = fetch_data('AL30', start_date, end_date, data_source)
      al30c = fetch_data('AL30C', start_date, end_date, data_source)

      if not al30.empty and not al30c.empty:
          ccl = al30['Adj Close'] / al30c['Adj Close']
      else:
          st.warning("No se pudo obtener CCL usando AL30/AL30C")
          return None

  elif data_source == 'AnálisisTécnico.com.ar':
      # Get CCL->PROMEDIO data
      ccl = fetch_data('CCL->PROMEDIO', start_date, end_date, data_source)
      if not ccl.empty:
          ccl = ccl['Adj Close']
      else:
          st.warning("No se pudo obtener CCL->PROMEDIO")
          return None

  # Forward fill and backward fill to handle missing values
  ccl = ccl.fillna(method='ffill').fillna(method='bfill')
  return ccl

if st.button('Obtener Datos y Graficar'):
  try:
      all_tickers = list(set([main_stock] + extra_stocks))

      # Initialize DataFrames
      adj_close = pd.DataFrame()
      volume = pd.DataFrame()

      # Fetch data for each ticker
      for ticker in all_tickers:
          data = fetch_data(ticker, start_date, end_date, data_source)
          if isinstance(data, pd.DataFrame) and not data.empty:
              if 'Adj Close' in data.columns and 'Volume' in data.columns:
                  adj_close[ticker] = data['Adj Close'].astype(float)
                  volume[ticker] = data['Volume'].astype(float)
                  st.write(f"Datos obtenidos para {ticker}")

      # Basic validation
      if adj_close.empty or main_stock not in adj_close.columns:
          st.error("No se pudieron obtener datos válidos")
          st.stop()

      # Create figure
      fig = go.Figure()
      colors = ['orange', 'blue', 'green', 'red', 'purple', 'cyan']

      # Process each comparison stock
      # After calculating the ratio for each stock comparison
      for idx, stock in enumerate(extra_stocks):
          if stock not in adj_close.columns:
              continue

          # Calculate ratio (your existing code)
          valid_mask = (adj_close[main_stock].notna() & adj_close[stock].notna())

          if calculation_method == 'Precio * Volumen Ratio':
              if stock in volume.columns and main_stock in volume.columns:
                  valid_mask = valid_mask & volume[main_stock].notna() & volume[stock].notna()
                  ratio = (adj_close[main_stock][valid_mask] * volume[main_stock][valid_mask]) / \
                          (adj_close[stock][valid_mask] * volume[stock][valid_mask])
              else:
                  ratio = adj_close[main_stock][valid_mask] / adj_close[stock][valid_mask]
          else:
              ratio = adj_close[main_stock][valid_mask] / adj_close[stock][valid_mask]

          # Calculate the mean of the ratio
          ratio_mean = ratio.mean()
          ratio_std = ratio.std()

          # Convert to percentage if needed (your existing code)
          # Calculate rolling statistics
          rolling_mean = ratio.rolling(window=20).mean()  # 20-day rolling mean
          rolling_std = ratio.rolling(window=20).std()  # 20-day rolling std
          upper_band = rolling_mean + (2 * rolling_std)
          lower_band = rolling_mean - (2 * rolling_std)
          upper_band_mean = ratio_mean + (2 * ratio_std)
          lower_band_mean = ratio_mean - (2 * ratio_std)

          # Convert to percentage if needed
          if view_as_percentages:
              reference_idx = ratio.index[ratio.index.get_indexer([reference_date], method='nearest')[0]]
              reference_value = ratio[reference_idx]
              ratio = (ratio / reference_value - 1) * 100
              rolling_mean = (rolling_mean / reference_value - 1) * 100
              upper_band = (upper_band / reference_value - 1) * 100
              lower_band = (lower_band / reference_value - 1) * 100
              upper_band_mean = (upper_band / reference_value - 1) * 100
              lower_band_mean = (lower_band / reference_value - 1) * 100
              name_suffix = f"({reference_value:.2f})"
          else:
              name_suffix = ""

          # Define rgba colors for the bands
          rgba_colors = [
              'rgba(255, 165, 0, 0.1)',  # orange
              'rgba(0, 0, 255, 0.1)',  # blue
              'rgba(0, 255, 0, 0.1)',  # green
              'rgba(255, 0, 0, 0.1)',  # red
              'rgba(128, 0, 128, 0.1)',  # purple
              'rgba(0, 255, 255, 0.1)'  # cyan
          ]

          # Add main ratio trace
          fig.add_trace(go.Scatter(
              x=ratio.index,
              y=ratio.values,
              mode='lines',
              name=f'{main_stock}/{stock} {name_suffix}',
              line=dict(color=colors[idx % len(colors)])
          ))

          # Add rolling mean line
          fig.add_trace(go.Scatter(
              x=rolling_mean.index,
              y=rolling_mean.values,
              mode='lines',
              name=f'MA(20) {main_stock}/{stock}',
              line=dict(
                  color=colors[idx % len(colors)],
                  dash='dash',
                  width=1
              ),
              opacity=0.7
          ))

          # Add upper and lower standard deviation bands
          fig.add_trace(go.Scatter(
              x=upper_band.index,
              y=upper_band.values,
              mode='lines',
              name=f'+2σ {main_stock}/{stock}',
              line=dict(
                  color=colors[idx % len(colors)],
                  dash='dot',
                  width=1
              ),
              opacity=0.5
          ))

          fig.add_trace(go.Scatter(
              x=lower_band.index,
              y=lower_band.values,
              mode='lines',
              name=f'-2σ {main_stock}/{stock}',
              line=dict(
                  color=colors[idx % len(colors)],
                  dash='dot',
                  width=1
              ),
              opacity=0.5
          ))

          # Add filled area between standard deviation bands
          if show_filled_area:
    # Add filled area between standard deviation bands  
          fig.add_trace(go.Scatter(  
              x=upper_band.index.tolist() + lower_band.index.tolist()[::-1],
              y=upper_band.values.tolist() + lower_band.values.tolist()[::-1],
              fill='toself',
              fillcolor=rgba_colors[idx % len(rgba_colors)],
              line=dict(width=0),
              showlegend=False,
              name=f'2σ Band {main_stock}/{stock}'
          ))

          # Add mean line
          fig.add_trace(go.Scatter(
              x=[ratio.index[0], ratio.index[-1]],  # Start and end of the time period
              y=[ratio_mean, ratio_mean],
              mode='lines',
              name=f'Mean {main_stock}/{stock}',
              line=dict(
                  color=colors[idx % len(colors)],
                  dash='dash',  # Makes the line dashed
                  width=1
              ),
              opacity=0.7
          ))

          # Add upper and lower standard deviation bands
          fig.add_trace(go.Scatter(
              x=[ratio.index[0], ratio.index[-1]],
              y=[upper_band_mean, upper_band_mean],
              mode='lines',
              name=f'+2σ {main_stock}/{stock}',
              line=dict(
                  color=colors[idx % len(colors)],
                  dash='dot',
                  width=1
              ),
              opacity=0.5
          ))

          fig.add_trace(go.Scatter(
              x=[ratio.index[0], ratio.index[-1]],
              y=[lower_band_mean, lower_band_mean],
              mode='lines',
              name=f'-2σ {main_stock}/{stock}',
              line=dict(
                  color=colors[idx % len(colors)],
                  dash='dot',
                  width=1
              ),
              opacity=0.5
          ))

          # Calculate SMA
          if len(ratio) >= sma_period:
              sma = ratio.rolling(window=sma_period).mean()
          else:
              sma = pd.Series(index=ratio.index, dtype=float)


          # Add SMA trace
          if not sma.empty:
              fig.add_trace(go.Scatter(
                  x=sma.index,
                  y=sma.values,
                  mode='lines',
                  name=f'SMA {sma_period} {main_stock}/{stock}',
                  line=dict(color=colors[idx % len(colors)], dash='dot')
              ))

          # Add individual price series
          # Get CCL ratio if needed
          ccl_ratio = None
          if normalize_by_ccl:
              ccl_ratio = get_ccl_ratio(data_source, start_date, end_date)
              if ccl_ratio is None:
                  st.warning("Usando precios sin normalizar por CCL")

          # Add individual price series
          for ticker in [main_stock, stock]:
              prices = adj_close[ticker]
              # And in the main plotting section, when applying CCL normalization:
              if normalize_by_ccl and ccl_ratio is not None:
                  # Make sure the price index is timezone-naive
                  if prices.index.tz is not None:
                      prices.index = prices.index.tz_localize(None)
                  if ccl_ratio.index.tz is not None:
                      ccl_ratio.index = ccl_ratio.index.tz_localize(None)

                  # Create a complete date range
                  full_index = pd.date_range(start=min(prices.index.min(), ccl_ratio.index.min()),
                                             end=max(prices.index.max(), ccl_ratio.index.max()),
                                             freq='D')

                  # Reindex and forward fill both series
                  prices_filled = prices.reindex(full_index).ffill()
                  ccl_ratio_filled = ccl_ratio.reindex(full_index).ffill()

                  # Calculate normalized prices
                  normalized_prices = prices_filled / ccl_ratio_filled

                  fig.add_trace(go.Scatter(
                      x=normalized_prices.index,
                      y=normalized_prices,
                      mode='lines',
                      name=f'{ticker} Price (CCL adj)',
                      opacity=0.3,
                      yaxis='y2'
                  ))
              else:
                  fig.add_trace(go.Scatter(
                      x=prices.index,
                      y=prices,
                      mode='lines',
                      name=f'{ticker} Price',
                      opacity=0.3,
                      yaxis='y2'
                  ))



      # Update layout
      # Update layout
      # Update layout
      # Update layout
      # Update layout
      # Update layout
      fig.update_layout(
          title='Ratios de Activos',
          xaxis_title='Fecha',
          yaxis_title='Ratio' if not view_as_percentages else 'Porcentaje',
          xaxis_rangeslider_visible=False,
          yaxis=dict(
              showgrid=True,
              type='linear'
          ),
          yaxis2=dict(
              title='Precio' + (' (Ajustado por CCL)' if normalize_by_ccl else ''),
              overlaying='y',
              side='right',
              showgrid=False,
              type='log' if use_log_scale else 'linear',
              tickformat='.2f'
          ),
          showlegend=True,
          legend=dict(
              orientation="h",
              yanchor="bottom",
              y=1.02,
              xanchor="right",
              x=1
          )
      )

      # Add watermark
      fig.add_annotation(
          text="MTaurus - X: @MTaurus_ok",
          xref="paper", yref="paper",
          x=0.5, y=0.5,
          showarrow=False,
          font=dict(size=30, color="rgba(150,150,150,0.3)"),
          textangle=-30,
          opacity=0.3
      )

      # Display the figure
      st.plotly_chart(fig, use_container_width=True)

  except Exception as e:
      st.error(f"Se produjo un error: {str(e)}")
      st.write("Detalles del error:", e.__class__.__name__)

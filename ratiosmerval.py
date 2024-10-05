import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

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
with st.sidebar:
  # Main stock selection
  main_stock_input = st.text_input('Ingresar manualmente un ticker principal (si no está en la lista):', '').upper()
  main_stock = st.selectbox(
      'Seleccionar el ticker principal:',
      options=[main_stock_input] + tickers if main_stock_input else tickers,
      index=0 if main_stock_input else 0
  )

  # Additional tickers selection
  extra_stocks_input = st.text_input('Ingresar manualmente tickers adicionales (separados por comas):', '').upper()
  extra_stocks_manual = [ticker.strip() for ticker in extra_stocks_input.split(',') if ticker.strip()]
  extra_stocks_options = extra_stocks_manual + tickers
  extra_stocks = st.multiselect(
      'Seleccionar hasta 6 tickers adicionales:',
      options=extra_stocks_options,
      default=extra_stocks_manual[:6]  # Preselect manually entered tickers, up to 6
  )

  # Date inputs
  max_start_date = pd.to_datetime("2024-09-30")
  start_date = st.date_input("Fecha de inicio", pd.to_datetime("1980-01-01"), max_value=max_start_date)
  end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"), min_value=start_date)

  # Ensure start_date and end_date are timezone-naive
  start_date = pd.Timestamp(start_date).normalize()
  end_date = pd.Timestamp(end_date).normalize()

  # Determine the most recent valid date for the reference date
  today = pd.Timestamp("today").normalize()
  most_recent_valid_date = get_recent_valid_date(start_date, today)
  reference_date = st.date_input("Fecha de referencia para visualizar como porcentajes:", most_recent_valid_date)

  # Ensure reference_date is timezone-naive
  reference_date = pd.Timestamp(reference_date).normalize()

  # Checkbox to choose percentage view
  view_as_percentages = st.checkbox('Ver como porcentajes en vez de ratios')

  # SMA input field
  sma_period = st.number_input('Periodo de SMA', min_value=1, value=20, key='sma_period')

  # Selection for calculation method
  calculation_method = st.selectbox(
      'Seleccionar método de cálculo:',
      options=['Precio Ratio', 'Precio * Volumen Ratio']
  )

# Fetch and process data
if st.button('Obtener Datos y Graficar'):
  try:
      # Fetch data
      data = yf.download([main_stock] + extra_stocks, start=start_date, end=end_date, group_by='ticker')

      # Debug: Print the structure of `data`
      st.write("Data structure:", data.head())
      st.write("Columns available:", data.columns)

      # Ensure data is a DataFrame and check for MultiIndex columns
      if isinstance(data, pd.DataFrame):
          if isinstance(data.columns, pd.MultiIndex):
              # Extract 'Adj Close' and 'Volume' data from MultiIndex
              adj_close = pd.DataFrame({ticker: data[ticker]['Adj Close'] for ticker in data.columns.levels[0]})
              volume = pd.DataFrame({ticker: data[ticker]['Volume'] for ticker in data.columns.levels[0]})
              data = adj_close
          elif 'Adj Close' in data.columns:
              data = data['Adj Close']
          else:
              st.error("Error: 'Adj Close' column not found in data.")
              st.stop()
      elif isinstance(data, pd.Series):
          data = pd.DataFrame(data).T
          data.columns = [main_stock] + extra_stocks
      else:
          st.error("Error: `data` es ni DataFrame ni Series.")
          st.stop()  # Stop Streamlit execution

      # Remove timezone information from the date index
      if data.index.tz:
          data.index = data.index.tz_localize(None)

      # Fill missing data with the last available value
      data.ffill(inplace=True)

      # Check if main stock exists in data
      if main_stock not in data.columns:
          st.error(f"No se encontró el ticker principal '{main_stock}' en los datos.")
          st.stop()  # Stop Streamlit execution
      else:
          # Plot setup
          fig = go.Figure()
          for stock in extra_stocks:
              if stock not in data.columns:
                  st.warning(f"No se encontró el ticker '{stock}' en los datos.")
                  continue
              
              # Check if volume data is available for the stock
              if calculation_method == 'Precio * Volumen Ratio':
                  if stock not in volume.columns:
                      st.warning(f"No se encontró la columna 'Volume' para el ticker '{stock}'. Usando solo el Precio Ratio.")
                      calculation_method = 'Precio Ratio'  # Fallback to Precio Ratio if Volume is not available

              # Calculate ratio based on the selected method
              if calculation_method == 'Precio * Volumen Ratio':
                  # Ensure both price and volume indices are timezone-naive
                  price_main = data[main_stock]
                  price_stock = data[stock]
                  volume_main = volume[main_stock]
                  volume_stock = volume[stock]

                  # Ensure all indices are timezone-naive
                  price_main.index = price_main.index.tz_localize(None)
                  price_stock.index = price_stock.index.tz_localize(None)
                  volume_main.index = volume_main.index.tz_localize(None)
                  volume_stock.index = volume_stock.index.tz_localize(None)

                  ratio = (volume_main) / (volume_stock)
              else:  # Default to 'Precio Ratio'
                  ratio = data[main_stock] / data[stock]

              # Ensure the ratio index is timezone-naive
              ratio.index = ratio.index.tz_localize(None)

              if view_as_percentages:
                  # Ensure reference_date and ratio index are timezone-naive
                  reference_date = pd.Timestamp(reference_date).normalize()
                  ratio.index = ratio.index.normalize()  # Convert ratio index to timezone-naive
              
                  # Find the nearest available date to the reference_date
                  if reference_date not in ratio.index:
                      differences = abs(ratio.index - reference_date)
                      closest_date = ratio.index[differences.argmin()]
                      reference_date = closest_date
                      st.warning(f"La fecha de referencia ha sido ajustada a la fecha más cercana disponible: {reference_date.date()}")
              
                  reference_value = ratio.loc[reference_date]
                  ratio = (ratio / reference_value - 1) * 100
                  name_suffix = f"({reference_value:.2f})"
                  
                  # Add vertical reference line
                  fig.add_shape(
                      type="line",
                      x0=reference_date, y0=ratio.min(), x1=reference_date, y1=ratio.max(),
                      line=dict(color="yellow", dash="dash"),
                      xref="x", yref="y"
                  )
                  
                  # Add a thin red line across zero in the Y-axis
                  fig.add_shape(
                      type="line",
                      x0=ratio.index.min(), y0=0, x1=ratio.index.max(), y1=0,
                      line=dict(color="red", width=1),  # Thin red line
                      xref="x", yref="y"
                  )
              else:
                  name_suffix = ""

              fig.add_trace(go.Scatter(
                  x=ratio.index,
                  y=ratio,
                  mode='lines',
                  name=f'{main_stock} / {stock} {name_suffix}'
              ))

              # If only one additional ticker is selected, show the SMA and histogram
              if len(extra_stocks) == 1:
                  # Calculate SMA
                  sma = ratio.rolling(window=sma_period).mean()

                  # Create figure with SMA
                  fig_sma = go.Figure()
                  fig_sma.add_trace(go.Scatter(
                      x=ratio.index,
                      y=ratio,
                      mode='lines',
                      name=f'{main_stock} / {stock}'
                  ))
                  fig_sma.add_trace(go.Scatter(
                      x=sma.index,
                      y=sma,
                      mode='lines',
                      name=f'SMA {sma_period}',
                      line=dict(color='orange')
                  ))
                  
                  # Average value line
                  average_value = ratio.mean()
                  fig_sma.add_trace(go.Scatter(
                      x=[ratio.index.min(), ratio.index.max()],
                      y=[average_value, average_value],
                      mode='lines',
                      name=f'Promedio ({average_value:.2f})',
                      line=dict(color='purple', dash='dot')
                  ))
                  
                  fig_sma.update_layout(
                      title=f'Ratio de {main_stock} con {stock} y SMA ({sma_period} días)',
                      xaxis_title='Fecha',
                      yaxis_title='Ratio' if not view_as_percentages else 'Porcentaje',
                      xaxis_rangeslider_visible=False,
                      yaxis=dict(showgrid=True),
                      xaxis=dict(showgrid=True)
                  )
                  
                  st.plotly_chart(fig_sma, use_container_width=True)
                  
                  # Histogram of dispersion
                  dispersion = ratio - sma
                  dispersion = dispersion.dropna()
                  
                  fig_hist = go.Figure()
                  fig_hist.add_trace(go.Histogram(
                      x=dispersion,
                      nbinsx=50
                  ))
                  
                  percentiles = [25, 50, 75]
                  for p in percentiles:
                      value = np.percentile(dispersion, p)
                      fig_hist.add_shape(
                          type="line",
                          x0=value, y0=0, x1=value, y1=dispersion.max() * 0.95,
                          line=dict(color="red", dash="dot"),
                          xref="x", yref="y"
                      )
                      fig_hist.add_annotation(
                          x=value, y=dispersion.max() * 0.95,
                          text=f'{p}th Percentile',
                          showarrow=True,
                          arrowhead=2
                      )

                  fig_hist.update_layout(
                      title='Histograma de Dispersión del Ratio',
                      xaxis_title='Dispersión',
                      yaxis_title='Frecuencia',
                      xaxis=dict(showgrid=True),
                      yaxis=dict(showgrid=True)
                  )
                  
                  st.plotly_chart(fig_hist, use_container_width=True)

          # Update main figure layout
          fig.update_layout(
              title='Ratios de Activos',
              xaxis_title='Fecha',
              yaxis_title='Ratio' if not view_as_percentages else 'Porcentaje',
              xaxis_rangeslider_visible=False,
              yaxis=dict(showgrid=True),
              xaxis=dict(showgrid=True)
          )
          fig.add_annotation(
              text="MTaurus - Twitter/X: MTaurus_ok",
              xref="paper", yref="paper",
              x=0.5, y=0.5, showarrow=False,
              font=dict(size=20, color="rgba(150, 150, 150, 0.4)"),
              xanchor="center", yanchor="middle",
              opacity=0.3
          )            
          st.plotly_chart(fig, use_container_width=True)
  except Exception as e:
      st.error(f"Se produjo un error: {e}")

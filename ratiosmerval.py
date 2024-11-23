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
    extra_stocks_options = list(set(extra_stocks_manual + tickers))  # Eliminar duplicados
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

    # **Nueva Opción: Escala Logarítmica para el Eje Y**
    # Esta opción solo está habilitada si 'view_as_percentages' está desactivado,
    # ya que una escala logarítmica no puede manejar valores negativos o cero.
    if view_as_percentages:
        st.info("La escala logarítmica está deshabilitada cuando se visualizan los datos como porcentajes.")
        use_log_scale = False
    else:
        use_log_scale = st.checkbox('Usar escala logarítmica para el eje Y', value=False)

# Fetch and process data
# Replace the data processing section with this:

# Fetch and process data
# Fetch and process data
if st.button('Obtener Datos y Graficar'):
  try:
      # Combinar el main_stock y extra_stocks para descargar todos juntos
      all_tickers = list(set([main_stock] + extra_stocks))  # Eliminar duplicados

      # Fetch data
      data = yf.download(all_tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)

      # Initialize empty DataFrames for adj_close and volume
      adj_close = pd.DataFrame()
      volume = pd.DataFrame()

      # Handle different data structures based on number of tickers
      if len(all_tickers) == 1:
          ticker = all_tickers[0]
          adj_close[ticker] = data['Adj Close']
          volume[ticker] = data['Volume']
      else:
          for ticker in all_tickers:
              try:
                  adj_close[ticker] = data[ticker]['Adj Close']
                  volume[ticker] = data[ticker]['Volume']
              except KeyError as e:
                  st.warning(f"No se pudieron obtener datos para {ticker}: {e}")
                  continue

      # Verify we have data
      if adj_close.empty or volume.empty:
          st.error("No se pudieron obtener datos válidos para los tickers seleccionados.")
          st.stop()

      # Remove timezone information if present
      adj_close.index = adj_close.index.tz_localize(None)
      volume.index = volume.index.tz_localize(None)

      # Debug information
      st.write("Estructura de Adj Close:", adj_close.head())
      st.write("Estructura de Volume:", volume.head())

      # Check if main stock exists in data
      if main_stock not in adj_close.columns:
          st.error(f"No se encontró el ticker principal '{main_stock}' en los datos.")
          st.stop()

      # Plot setup
      fig = go.Figure()
      colors = ['orange', 'blue', 'green', 'red', 'purple', 'cyan', 'magenta', 'yellow', 'black', 'brown']

      for idx, stock in enumerate(extra_stocks):
          if stock not in adj_close.columns:
              st.warning(f"No se encontró el ticker '{stock}' en los datos de 'Adj Close'.")
              continue

          # Variable local para determinar el método de cálculo para este ticker
          local_calculation_method = calculation_method

          # Get valid data ranges for both stocks
          main_valid = adj_close[main_stock].notna()
          stock_valid = adj_close[stock].notna()

          # Only keep dates where both stocks have valid data
          valid_dates = main_valid & stock_valid

          # Check if volume data is available for the main stock and the current stock
          if calculation_method == 'Precio * Volumen Ratio':
              if (main_stock not in volume.columns) or (stock not in volume.columns):
                  st.warning(f"No se encontraron datos de 'Volume' para '{stock}' o '{main_stock}'. Usando 'Precio Ratio' para este ticker.")
                  local_calculation_method = 'Precio Ratio'
              else:
                  # Also consider volume data validity
                  volume_main_valid = volume[main_stock].notna()
                  volume_stock_valid = volume[stock].notna()
                  valid_dates = valid_dates & volume_main_valid & volume_stock_valid

          # Calculate ratio only for valid dates
          # Calculate ratio only for valid dates
        if local_calculation_method == 'Precio * Volumen Ratio':
          price_main = adj_close[main_stock][valid_dates]
          price_stock = adj_close[stock][valid_dates]
          volume_main = volume[main_stock][valid_dates]
          volume_stock = volume[stock][valid_dates]
          ratio = (price_main * volume_main) / (price_stock * volume_stock)
        else:
          ratio = adj_close[main_stock][valid_dates] / adj_close[stock][valid_dates]
        
        if view_as_percentages:
          # Asegurar que reference_date esté en el índice
          if reference_date not in ratio.index:
              differences = abs(ratio.index - reference_date)
              closest_date = ratio.index[differences.argmin()]
              reference_date_adj = closest_date
              st.warning(f"La fecha de referencia ha sido ajustada a la fecha más cercana disponible: {reference_date_adj.date()}")
          else:
              reference_date_adj = reference_date
        
          reference_value = ratio.loc[reference_date_adj]
          ratio = (ratio / reference_value - 1) * 100
          name_suffix = f"({reference_value:.2f})"
        
          # Add vertical reference line
          fig.add_shape(
              type="line",
              x0=reference_date_adj, y0=ratio.min(), x1=reference_date_adj, y1=ratio.max(),
              line=dict(color="yellow", dash="dash"),
              xref="x", yref="y"
          )
        
          # Add a thin red line across zero in the Y-axis
          fig.add_shape(
              type="line",
              x0=ratio.index.min(), y0=0, x1=ratio.index.max(), y1=0,
              line=dict(color="red", width=1),
              xref="x", yref="y"
          )
        else:
          name_suffix = ""
        
        # Verificar si hay suficientes datos para calcular la SMA
        if len(ratio) < sma_period:
          st.warning(f"No hay suficientes datos para calcular la SMA de {sma_period} días para el ticker '{stock}'.")
          sma = pd.Series([np.nan] * len(ratio), index=ratio.index)
        else:
          # Calculate SMA
          sma = ratio.rolling(window=sma_period).mean()
        
        # Agregar el ratio al gráfico principal
        fig.add_trace(go.Scatter(
          x=ratio.index,
          y=ratio,
          mode='lines',
          name=f'{main_stock} / {stock} {name_suffix}'
        ))
        
        # Agregar la SMA al gráfico principal con color único
        fig.add_trace(go.Scatter(
          x=sma.index,
          y=sma,
          mode='lines',
          name=f'SMA {sma_period} {main_stock} / {stock}',
          line=dict(color=colors[idx % len(colors)], dash='dot')
        ))

        # Si se selecciona solo un ticker adicional, mostrar SMA y histograma
        if len(extra_stocks) == 1:
            # Crear figura con SMA
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
                line=dict(color=colors[idx % len(colors)], dash='dot')
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

            # Histograma de dispersión
            dispersion = ratio - sma
            dispersion = dispersion.dropna()

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=dispersion,
                nbinsx=50
            ))

            if not dispersion.empty:
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

        # **Configuración del Eje Y según la Selección del Usuario**
        yaxis_type = 'log' if use_log_scale else 'linear'

        # Actualizar el layout del gráfico principal
        fig.update_layout(
            title='Ratios de Activos',
            xaxis_title='Fecha',
            yaxis_title='Ratio' if not view_as_percentages else 'Porcentaje',
            xaxis_rangeslider_visible=False,
            yaxis=dict(showgrid=True, type=yaxis_type),
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

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
    
    # Adjust this function if you have a list of holidays
    # For example, if you have a list of holidays, add a check to exclude them
    return end_date

# Streamlit UI
st.title('Análisis de Ratios de Activos del MERVAL. De MTAURUS - X: https://x.com/MTaurus_ok')

# Main stock selection
main_stock_input = st.text_input('Ingresar manualmente un ticker principal (si no está en la lista):', '').upper()
main_stock = st.selectbox(
    'Seleccionar el ticker principal:',
    options=[main_stock_input] + tickers if main_stock_input else tickers,
    index=0 if main_stock_input else 0
)

# Additional tickers selection
extra_stocks_input = st.text_input('Ingresar manualmente tickers adicionales (separados por comas):', '').upper()

# Split and clean the manually entered tickers
extra_stocks_manual = [ticker.strip() for ticker in extra_stocks_input.split(',') if ticker.strip()]
extra_stocks_options = extra_stocks_manual + tickers

extra_stocks = st.multiselect(
    'Seleccionar hasta 6 tickers adicionales:',
    options=extra_stocks_options,
    default=extra_stocks_manual[:6]  # Preselect manually entered tickers, up to 6
)

# Date inputs
start_date = st.date_input("Fecha de inicio", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"))

# Determine the most recent valid date for the reference date
today = pd.to_datetime("today")
most_recent_valid_date = get_recent_valid_date(start_date, today)
reference_date = st.date_input("Fecha de referencia para visualizar como porcentajes:", most_recent_valid_date)

# Checkbox to choose percentage view
view_as_percentages = st.checkbox('Ver como porcentajes en vez de ratios')

# Fetch and process data
if st.button('Obtener Datos y Graficar'):
    data = yf.download([main_stock] + extra_stocks, start=start_date, end=end_date)['Adj Close']
    
    # Fill missing data with the last available value
    data.fillna(method='ffill', inplace=True)

    # Check if main stock exists in data
    if main_stock not in data.columns:
        st.error(f"No se encontró el ticker principal '{main_stock}' en los datos.")
    else:
        fig = go.Figure()

        for stock in extra_stocks:
            if stock not in data.columns:
                st.warning(f"No se encontró el ticker '{stock}' en los datos.")
                continue
            
            ratio = data[main_stock] / data[stock]

            if view_as_percentages:
                reference_date = pd.Timestamp(reference_date)

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
            else:
                name_suffix = ""

            fig.add_trace(go.Scatter(
                x=ratio.index,
                y=ratio,
                mode='lines',
                name=f'{main_stock} / {stock} {name_suffix}'
            ))

            # If only one additional ticker is selected, show the SMA
            if len(extra_stocks) == 1:
                # Add SMA period input
                sma_period = st.number_input('Periodo del SMA (solo si un ticker adicional está seleccionado):', min_value=1, value=20)

                # Calculate and plot SMA
                sma = ratio.rolling(window=sma_period).mean()
                fig.add_trace(go.Scatter(
                    x=ratio.index,
                    y=sma,
                    mode='lines',
                    name=f'SMA {sma_period} días',
                    line=dict(color='orange', width=2)
                ))

                # Calculate and plot histogram of dispersion
                dispersion = ratio - sma
                fig2 = go.Figure()

                fig2.add_trace(go.Histogram(
                    x=dispersion,
                    nbinsx=50,
                    marker_color='blue'
                ))

                # Calculate and display max and min dispersion
                max_dispersion = dispersion.max()
                min_dispersion = dispersion.min()
                fig2.update_layout(
                    title='Histograma de Dispersión',
                    xaxis_title='Dispersión',
                    yaxis_title='Frecuencia',
                    annotations=[
                        dict(
                            x=max_dispersion, y=0,
                            xref='x', yref='y',
                            text=f'Máx: {max_dispersion:.2f}',
                            showarrow=True,
                            arrowhead=2,
                            ax=0,
                            ay=-40
                        ),
                        dict(
                            x=min_dispersion

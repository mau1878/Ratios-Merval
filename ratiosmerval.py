import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Streamlit web interface for selecting tickers and date range
st.title('Análisis de Ratios entre Acciones del MERVAL')

# List of tickers
tickers = [
    "GGAL.BA", "YPFD.BA", "PAMP.BA", "TXAR.BA", "ALUA.BA", "CRES.BA", "SUPV.BA", "CEPU.BA",
    "BMA.BA", "TGSU2.BA", "TRAN.BA", "EDN.BA", "LOMA.BA", "MIRG.BA", "DGCU2.BA", "BBAR.BA",
    "MOLI.BA", "TGNO4.BA", "CGPA2.BA", "COME.BA", "IRSA.BA", "BYMA.BA", "TECO2.BA", "METR.BA",
    "CECO2.BA", "BHIP.BA", "AGRO.BA", "LEDE.BA", "CVH.BA", "HAVA.BA", "AUSO.BA", "VALO.BA",
    "SEMI.BA", "INVJ.BA", "CTIO.BA", "MORI.BA", "HARG.BA", "GCLA.BA", "SAMI.BA", "BOLT.BA",
    "MOLA.BA", "CAPX.BA", "OEST.BA", "LONG.BA", "GCDI.BA", "GBAN.BA", "CELU.BA", "FERR.BA",
    "CADO.BA", "GAMI.BA", "PATA.BA", "CARC.BA", "BPAT.BA", "RICH.BA", "INTR.BA", "GARO.BA",
    "FIPL.BA", "GRIM.BA", "DYCA.BA", "POLL.BA", "DOME.BA", "ROSE.BA", "MTR.BA"
]

# Ticker selection with manual input allowed
main_stock = st.selectbox('Seleccionar el ticker principal:', tickers, index=tickers.index("GGAL.BA"))
main_stock = main_stock.upper()
additional_stocks = st.multiselect('Seleccionar hasta 6 tickers adicionales:', tickers, default=["YPFD.BA"], max_selections=6)
additional_stocks = [ticker.upper() for ticker in additional_stocks]

# Date range selection
start_date = st.date_input("Fecha de inicio", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"))

# Reference date for percentage visualization
today = datetime.today()
if today.weekday() >= 5:  # Saturday or Sunday
    today -= timedelta(days=today.weekday() - 4)  # Adjust to the previous Friday

reference_date = st.date_input("Fecha de referencia para visualizar como porcentajes:", today)

# Button to fetch data and perform analysis
if st.button('Fetch Data'):
    all_stocks = [main_stock] + additional_stocks
    data = yf.download(all_stocks, start=start_date, end=end_date)['Adj Close']

    # Fill missing data with the last available value
    data = data.fillna(method='ffill')

    # Process and plot data
    fig = go.Figure()

    for stock in additional_stocks:
        # Calculate the ratio
        ratio = data[main_stock] / data[stock]

        # Handle the case where the reference date is not in the data
        if reference_date not in ratio.index:
            closest_date = min(ratio.index, key=lambda d: abs(d - pd.to_datetime(reference_date)))
            st.warning(f"La fecha de referencia {reference_date} no existe en los datos. Usando la fecha más cercana: {closest_date}.")
            reference_date = closest_date

        # Visualization as percentages
        if st.checkbox("Visualizar como porcentajes"):
            reference_value = ratio.loc[reference_date]
            ratio = (ratio / reference_value - 1) * 100
            fig.add_shape(type='line', x0=reference_date, x1=reference_date, y0=ratio.min(), y1=ratio.max(),
                          line=dict(color='yellow', dash='dash'))
            fig.add_shape(type='line', x0=ratio.index.min(), x1=ratio.index.max(), y0=0, y1=0,
                          line=dict(color='red', dash='dash'))
            y_axis_title = 'Ratio (%)'
        else:
            y_axis_title = 'Ratio'
            if 0.95 <= ratio.min() <= 1.05 or 0.95 <= ratio.max() <= 1.05:
                fig.add_shape(type='line', x0=ratio.index.min(), x1=ratio.index.max(), y0=1, y1=1,
                              line=dict(color='red', dash='dash'))

        # Plot the ratio
        fig.add_trace(go.Scatter(
            x=ratio.index,
            y=ratio,
            mode='lines',
            name=f'Ratio {main_stock}/{stock}'
        ))

    # Add grid lines
    fig.update_layout(
        title=f'Ratios de {main_stock} con otros tickers',
        xaxis_title='Fecha',
        yaxis_title=y_axis_title,
        xaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='LightGray'),
        yaxis=dict(showgrid=True, gridwidth=0.5, gridcolor='LightGray'),
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

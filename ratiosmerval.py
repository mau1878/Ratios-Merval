import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# Lista de tickers disponibles
tickers = [
    "GGAL.BA", "YPFD.BA", "PAMP.BA", "TXAR.BA", "ALUA.BA", "CRES.BA", "SUPV.BA", "CEPU.BA", "BMA.BA", "TGSU2.BA", 
    "TRAN.BA", "EDN.BA", "LOMA.BA", "MIRG.BA", "DGCU2.BA", "BBAR.BA", "MOLI.BA", "TGNO4.BA", "CGPA2.BA", "COME.BA", 
    "IRSA.BA", "BYMA.BA", "TECO2.BA", "METR.BA", "CECO2.BA", "BHIP.BA", "AGRO.BA", "LEDE.BA", "CVH.BA", "HAVA.BA", 
    "AUSO.BA", "VALO.BA", "SEMI.BA", "INVJ.BA", "CTIO.BA", "MORI.BA", "HARG.BA", "GCLA.BA", "SAMI.BA", "BOLT.BA", 
    "MOLA.BA", "CAPX.BA", "OEST.BA", "LONG.BA", "GCDI.BA", "GBAN.BA", "CELU.BA", "FERR.BA", "CADO.BA", "GAMI.BA", 
    "PATA.BA", "CARC.BA", "BPAT.BA", "RICH.BA", "INTR.BA", "GARO.BA", "FIPL.BA", "GRIM.BA", "DYCA.BA", "POLL.BA", 
    "DOME.BA", "ROSE.BA", "MTR.BA"
]

st.title('Análisis de Ratios entre Acciones')

# Selección de la acción principal
main_ticker = st.selectbox("Seleccionar el ticker principal", tickers)

# Selección de hasta seis tickers adicionales
extra_tickers = st.multiselect("Seleccionar hasta seis tickers adicionales", tickers)

# Selección de fecha de inicio y finalización
start_date = st.date_input("Fecha de inicio", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"))  # Default to the present date

# Selección de fecha de referencia para mostrar los ratios como porcentajes
reference_date = st.date_input("Seleccionar fecha de referencia para porcentajes", pd.to_datetime("2023-01-01"))

# Botón para realizar el análisis
if st.button('Realizar Análisis'):
    if main_ticker and extra_tickers:
        # Fetching data
        data = yf.download([main_ticker] + extra_tickers, start=start_date, end=end_date)['Adj Close']

        # Calculando los ratios y porcentajes
        ratios = pd.DataFrame()
        for ticker in extra_tickers:
            ratios[f'{main_ticker}/{ticker}'] = data[main_ticker] / data[ticker]

        # Mostrar los ratios como porcentaje respecto al valor en la fecha de referencia
        if reference_date in ratios.index:
            ref_values = ratios.loc[reference_date]
            ratios_percent = (ratios / ref_values) * 100
        else:
            st.error("La fecha de referencia seleccionada no está en el rango de fechas disponible.")
            ratios_percent = ratios.copy()

        # Graficar los ratios
        fig = go.Figure()
        for column in ratios.columns:
            fig.add_trace(go.Scatter(
                x=ratios.index,
                y=ratios_percent[column],
                mode='lines',
                name=column
            ))

        fig.update_layout(
            title='Ratios entre Acciones',
            xaxis_title='Fecha',
            yaxis_title='Ratio (%)',
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Debe seleccionar una acción principal y al menos un ticker adicional.")

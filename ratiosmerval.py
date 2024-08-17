import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# List of available tickers
tickers = [
    'GGAL.BA', 'YPFD.BA', 'PAMP.BA', 'TXAR.BA', 'ALUA.BA', 'CRES.BA', 'SUPV.BA', 'CEPU.BA', 'BMA.BA', 
    'TGSU2.BA', 'TRAN.BA', 'EDN.BA', 'LOMA.BA', 'MIRG.BA', 'DGCU2.BA', 'BBAR.BA', 'MOLI.BA', 'TGNO4.BA', 
    'CGPA2.BA', 'COME.BA', 'IRSA.BA', 'BYMA.BA', 'TECO2.BA', 'METR.BA', 'CECO2.BA', 'BHIP.BA', 'AGRO.BA', 
    'LEDE.BA', 'CVH.BA', 'HAVA.BA', 'AUSO.BA', 'VALO.BA', 'SEMI.BA', 'INVJ.BA', 'CTIO.BA', 'MORI.BA', 
    'HARG.BA', 'GCLA.BA', 'SAMI.BA', 'BOLT.BA', 'MOLA.BA', 'CAPX.BA', 'OEST.BA', 'LONG.BA', 'GCDI.BA', 
    'GBAN.BA', 'CELU.BA', 'FERR.BA', 'CADO.BA', 'GAMI.BA', 'PATA.BA', 'CARC.BA', 'BPAT.BA', 'RICH.BA', 
    'INTR.BA', 'GARO.BA', 'FIPL.BA', 'GRIM.BA', 'DYCA.BA', 'POLL.BA', 'DOME.BA', 'ROSE.BA', 'MTR.BA'
]

# Streamlit UI setup
st.title('Análisis de Ratios entre Acciones')

# Select main ticker
main_ticker = st.selectbox("Seleccionar el ticker principal para analizar:", tickers)

# Select up to six additional tickers
extra_tickers = st.multiselect("Seleccionar hasta seis tickers adicionales:", tickers, max_selections=6)

# Date input
start_date = st.date_input("Fecha de inicio", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"))

# Button to fetch data and plot
if st.button('Mostrar Análisis'):
    # Fetch historical data
    main_stock = yf.Ticker(main_ticker)
    main_hist = main_stock.history(start=start_date, end=end_date)
    main_hist['Price'] = main_hist['Close']

    fig = go.Figure()

    # Plot main stock price
    fig.add_trace(go.Scatter(
        x=main_hist.index,
        y=main_hist['Price'],
        mode='lines',
        name=main_ticker,
        line=dict(color='blue')
    ))

    # Plot ratios with extra tickers
    for ticker in extra_tickers:
        extra_stock = yf.Ticker(ticker)
        extra_hist = extra_stock.history(start=start_date, end=end_date)
        extra_hist['Price'] = extra_hist['Close']

        # Calculate ratio
        ratio = main_hist['Price'] / extra_hist['Price']

        fig.add_trace(go.Scatter(
            x=main_hist.index,
            y=ratio,
            mode='lines',
            name=f'{main_ticker}/{ticker}',
            line=dict()
        ))

    fig.update_layout(
        title=f'Análisis de Ratios: {main_ticker} vs Otros Tickers',
        xaxis_title='Fecha',
        yaxis_title='Ratio',
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig, use_container_width=True)

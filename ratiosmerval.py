import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Tickers list
tickers = [
    "GGAL.BA", "YPFD.BA", "PAMP.BA", "TXAR.BA", "ALUA.BA", "CRES.BA", "SUPV.BA", "CEPU.BA", "BMA.BA", 
    "TGSU2.BA", "TRAN.BA", "EDN.BA", "LOMA.BA", "MIRG.BA", "DGCU2.BA", "BBAR.BA", "MOLI.BA", "TGNO4.BA", 
    "CGPA2.BA", "COME.BA", "IRSA.BA", "BYMA.BA", "TECO2.BA", "METR.BA", "CECO2.BA", "BHIP.BA", "AGRO.BA", 
    "LEDE.BA", "CVH.BA", "HAVA.BA", "AUSO.BA", "VALO.BA", "SEMI.BA", "INVJ.BA", "CTIO.BA", "MORI.BA", 
    "HARG.BA", "GCLA.BA", "SAMI.BA", "BOLT.BA", "MOLA.BA", "CAPX.BA", "OEST.BA", "LONG.BA", "GCDI.BA", 
    "GBAN.BA", "CELU.BA", "FERR.BA", "CADO.BA", "GAMI.BA", "PATA.BA", "CARC.BA", "BPAT.BA", "RICH.BA", 
    "INTR.BA", "GARO.BA", "FIPL.BA", "GRIM.BA", "DYCA.BA", "POLL.BA", "DOME.BA", "ROSE.BA", "MTR.BA"
]

# Streamlit interface for inputs
st.title('Análisis de Ratios entre Acciones')

# User selects the main stock
main_stock = st.selectbox("Seleccionar el ticker principal:", tickers)

# User selects up to 6 extra stocks
extra_stocks = st.multiselect("Seleccionar hasta 6 tickers adicionales:", tickers, max_selections=6)

# Date range selection
start_date = st.date_input("Fecha de inicio", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"))
reference_date = st.date_input("Seleccionar fecha de referencia para porcentajes:", pd.to_datetime("2023-01-01"))

# User chooses to see ratios or percentages
show_as_percentage = st.checkbox("Mostrar ratios como porcentaje de la fecha de referencia")

# Fetch data and calculate ratios
if st.button('Mostrar gráficos'):
    if extra_stocks:
        main_data = yf.download(main_stock, start=start_date, end=end_date)['Close']
        fig = go.Figure()

        for stock in extra_stocks:
            extra_data = yf.download(stock, start=start_date, end=end_date)['Close']
            ratio = main_data / extra_data

            # Check if the reference date exists in the ratio data
            if reference_date not in ratio.index:
                st.error(f"La fecha de referencia {reference_date} no existe en los datos. Por favor, elija otra fecha.")
            else:
                if show_as_percentage:
                    reference_value = ratio.loc[reference_date]
                    ratio = (ratio / reference_value) * 100

                fig.add_trace(go.Scatter(
                    x=ratio.index,
                    y=ratio,
                    mode='lines',
                    name=f'{main_stock}/{stock}'
                ))

        fig.update_layout(
            title=f'Ratios de {main_stock} respecto a otros activos',
            xaxis_title='Fecha',
            yaxis_title='Ratio' if not show_as_percentage else 'Porcentaje (%)',
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Por favor seleccione al menos un ticker adicional.")

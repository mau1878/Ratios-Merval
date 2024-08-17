import yfinance as yf
import pandas as pd
import numpy as np
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

# Streamlit UI
st.title('Análisis de Ratios de Activos del MERVAL')

main_stock = st.selectbox('Seleccionar el ticker principal:', tickers)
extra_stocks = st.multiselect('Seleccionar hasta 6 tickers adicionales:', tickers, default=tickers[1:7])
start_date = st.date_input("Fecha de inicio", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Fecha de finalización", pd.to_datetime("today"))
reference_date = st.date_input("Fecha de referencia para visualizar como porcentajes:", pd.to_datetime("2023-06-01"))

# Checkbox to choose percentage view
view_as_percentages = st.checkbox('Ver como porcentajes en vez de ratios')

# Fetch and process data
if st.button('Obtener Datos y Graficar'):
    data = yf.download([main_stock] + extra_stocks, start=start_date, end=end_date)['Adj Close']

    fig = go.Figure()

    for stock in extra_stocks:
        ratio = data[main_stock] / data[stock]

        if view_as_percentages:
            # Find the nearest available date to the reference_date
            if reference_date not in ratio.index:
                # Find the nearest date manually
                closest_date = min(ratio.index, key=lambda d: abs(d - reference_date))
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

        # Add horizontal line at 0% for percentages view
        if view_as_percentages:
            fig.add_shape(
                type="line",
                x0=ratio.index.min(), y0=0, x1=ratio.index.max(), y1=0,
                line=dict(color="red", dash="dash"),
                xref="x", yref="y"
            )
        else:
            # Add horizontal line at 1 if ratio values are close to 1
            if ratio.min() < 1.05 and ratio.max() > 0.95:
                fig.add_shape(
                    type="line",
                    x0=ratio.index.min(), y0=1, x1=ratio.index.max(), y1=1,
                    line=dict(color="red", dash="dash"),
                    xref="x", yref="y"
                )

    fig.update_layout(
        title=f'Ratios de {main_stock} con activos seleccionados',
        xaxis_title='Fecha',
        yaxis_title='Ratio' if not view_as_percentages else 'Porcentaje',
        xaxis_rangeslider_visible=False,
        yaxis=dict(showgrid=True),
        xaxis=dict(showgrid=True)
    )

    st.plotly_chart(fig, use_container_width=True)


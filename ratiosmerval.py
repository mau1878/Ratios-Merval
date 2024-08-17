import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Configuración de la aplicación Streamlit
st.title("Análisis de Ratios entre Acciones")

# Selección de las acciones
tickers = [
    'GGAL.BA', 'YPFD.BA', 'PAMP.BA', 'TXAR.BA', 'ALUA.BA', 'CRES.BA', 'SUPV.BA', 'CEPU.BA', 'BMA.BA', 'TGSU2.BA',
    'TRAN.BA', 'EDN.BA', 'LOMA.BA', 'MIRG.BA', 'DGCU2.BA', 'BBAR.BA', 'MOLI.BA', 'TGNO4.BA', 'CGPA2.BA', 'COME.BA',
    'IRSA.BA', 'BYMA.BA', 'TECO2.BA', 'METR.BA', 'CECO2.BA', 'BHIP.BA', 'AGRO.BA', 'LEDE.BA', 'CVH.BA', 'HAVA.BA',
    'AUSO.BA', 'VALO.BA', 'SEMI.BA', 'INVJ.BA', 'CTIO.BA', 'MORI.BA', 'HARG.BA', 'GCLA.BA', 'SAMI.BA', 'BOLT.BA',
    'MOLA.BA', 'CAPX.BA', 'OEST.BA', 'LONG.BA', 'GCDI.BA', 'GBAN.BA', 'CELU.BA', 'FERR.BA', 'CADO.BA', 'GAMI.BA',
    'PATA.BA', 'CARC.BA', 'BPAT.BA', 'RICH.BA', 'INTR.BA', 'GARO.BA', 'FIPL.BA', 'GRIM.BA', 'DYCA.BA', 'POLL.BA',
    'DOME.BA', 'ROSE.BA', 'MTR.BA'
]

main_ticker = st.selectbox("Selecciona la acción principal para analizar:", tickers)
extra_tickers = st.multiselect("Selecciona hasta 6 acciones adicionales:", tickers, max_selections=6)

reference_date = st.date_input("Selecciona la fecha de referencia para ver porcentajes:", pd.to_datetime("2023-01-01"))

# Opción de visualización
visualize_as_percentages = st.checkbox("Visualizar como porcentajes respecto a la fecha de referencia")

if st.button('Realizar Análisis'):
    if extra_tickers:
        # Descargar los datos históricos
        main_stock = yf.Ticker(main_ticker)
        extra_stocks = [yf.Ticker(ticker) for ticker in extra_tickers]

        main_data = main_stock.history(period="1y")
        extra_data = {ticker: stock.history(period="1y") for ticker, stock in zip(extra_tickers, extra_stocks)}

        # Calcular los ratios
        ratios = pd.DataFrame(index=main_data.index)
        for ticker in extra_tickers:
            ratios[ticker] = main_data['Close'] / extra_data[ticker]['Close']

        fig = go.Figure()

        if visualize_as_percentages:
            # Calcular los porcentajes en relación con la fecha de referencia
            reference_value = ratios.loc[reference_date]
            ratios_percent = (ratios / reference_value - 1) * 100

            for ticker in extra_tickers:
                fig.add_trace(go.Scatter(
                    x=ratios_percent.index,
                    y=ratios_percent[ticker],
                    mode='lines',
                    name=f'{main_ticker}/{ticker}'
                ))

            # Línea vertical amarilla en la fecha de referencia
            fig.add_vline(x=reference_date, line=dict(color="yellow", dash="dash"), name="Fecha de Referencia")
            # Línea horizontal roja en 0%
            fig.add_hline(y=0, line=dict(color="red", dash="dash"), name="0%")
        else:
            for ticker in extra_tickers:
                fig.add_trace(go.Scatter(
                    x=ratios.index,
                    y=ratios[ticker],
                    mode='lines',
                    name=f'{main_ticker}/{ticker}'
                ))
            # Línea horizontal en 1 en el eje Y
            fig.add_hline(y=1, line=dict(color="red", dash="dash"), name="Ratio = 1")

        # Agregar líneas de cuadrícula suaves
        fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGrey')
        fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGrey')

        # Configuración del diseño de la gráfica
        fig.update_layout(
            title=f'Análisis de Ratios: {main_ticker} contra otras acciones',
            xaxis_title='Fecha',
            yaxis_title='Ratio' if not visualize_as_percentages else 'Porcentaje (%)',
            xaxis_rangeslider_visible=False
        )

        # Mostrar la gráfica en Streamlit
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Por favor, selecciona al menos una acción adicional para comparar.")


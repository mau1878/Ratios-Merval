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
    
    # You might need to adjust this function if you have a list of holidays
    # For example, if you have a list of holidays, add a check to exclude them
    return end_date

# Streamlit UI
st.title('Análisis de Ratios de Activos del MERVAL')

# Main stock selection
main_stock_input = st.text_input('Ingresar manualmente un ticker principal (si no está en la lista):', '')
main_stock_input = main_stock_input.upper()
main_stock = st.selectbox(
    'Seleccionar el ticker principal:',
    options=[main_stock_input] + tickers if main_stock_input else tickers,
    index=0 if main_stock_input else 0  # Default to the manually entered ticker if provided
)

# Additional tickers selection
extra_stocks_input = st.text_input('Ingresar manualmente tickers adicionales (separados por comas):', '')

# Convert manually entered tickers to uppercase
manual_tickers = [ticker.strip().upper() for ticker in extra_stocks_input.split(',') if ticker]

# Combine manually entered tickers with predefined tickers, removing duplicates
combined_tickers = list(dict.fromkeys(manual_tickers + tickers))

extra_stocks = st.multiselect(
    'Seleccionar hasta 6 tickers adicionales:',
    options=combined_tickers,
    default=combined_tickers[:6]  # Default to the first 6 tickers in the combined list
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
                # Convert reference_date to pandas.Timestamp
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

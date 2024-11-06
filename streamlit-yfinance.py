import streamlit as st
import sqlite3
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from PIL import Image
import os



# Set page configuration
st.set_page_config(page_title="Financial Analysis Dashboard", layout="wide")

# CSS for the header
header_style = """
    <style>
        .header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 150px;
            background-color: #f1f2f6;
            z-index: 99999;
            display: flex;
            align-items: center;
            padding-left: 00px;
        }
        .content {
            margin-top: 0px;  /* Adjust this value to be slightly more than your header height */
        }
        .logo {
            height: 100px;  /* Adjust as needed */
            margin-right: 100px;
        }
    </style>
"""

st.markdown(header_style, unsafe_allow_html=True)

# Create a container for the header
header_container = st.container()

# Load the logo
logo_path = "/Users/davidscatterday/Documents/python projects/Stocks/assets/RFL.png"
logo = Image.open(logo_path)

# Sidebar with logo
with st.sidebar:
    st.image(logo, width=150)  # Adjust width as needed

# existing Streamlit app code
# Database connection
DB_PATH = "/Users/davidscatterday/Documents/python projects/NYC/nycprocurement.db"

def get_sector_data(sector):
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT Sector, Description, Primary_Subsector, Subsector_Weight, Harm_Magnitude, Population_Impact, Directional_Movement, Total_Score
    FROM stockracialharm
    WHERE Sector LIKE ?
    """
    df = pd.read_sql_query(query, conn, params=(f"%{sector}%",))
    conn.close()
    return df

def get_all_sectors():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT Sector FROM stockracialharm"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df['Sector'].tolist()

# Format market cap and enterprise value
def format_value(value):
    suffixes = ["", "K", "M", "B", "T"]
    suffix_index = 0
    while value >= 1000 and suffix_index < len(suffixes) - 1:
        value /= 1000
        suffix_index += 1
    return f"${value:.1f}{suffixes[suffix_index]}"

# Get all available sectors
all_sectors = get_all_sectors()

# Sidebar for user inputs
with st.sidebar:
    st.markdown("<h4 style='font-size: 18px;'>Public Equity Search</h4>", unsafe_allow_html=True)
    
    ticker = st.text_input("Enter a stock ticker (e.g. MSFT)", "")
    sector_search = st.selectbox("Select industry sector:", [""] + all_sectors)
    period = st.selectbox("Enter a timeframe", ("1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"), index=2)
    
    submit_button = st.button("Search")

# Main content area
st.markdown("<h2 style='font-size: 32px;'>Racial Justice Investment Intelligence Dashboard</h2>", unsafe_allow_html=True)

st.divider()

if submit_button:
    if not ticker or not sector_search:
        st.error("Please provide both a stock ticker and select a sector to search.")
    else:
        # Stock Market Data
        try:
            with st.spinner('Fetching stock data...'):
                stock = yf.Ticker(ticker)
                info = stock.info
                st.subheader(f"{ticker} - {info.get('longName', 'N/A')}")
                
                # Plot historical stock price data
                history = stock.history(period=period)
                
                if not history.empty:
                    # Check if 'Close' column exists
                    if 'Close' in history.columns:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=history.index, y=history['Close'], mode='lines', name='Close Price'))
                        fig.update_layout(
                            title=f'{ticker} Stock Price',
                            xaxis_title='Date',
                            yaxis_title='Price',
                            template='plotly_white'
                        )
                        st.plotly_chart(fig)
                    else:
                        st.error("'Close' price data not found in the retrieved history.")
                        st.write("Available columns:", history.columns.tolist())
                else:
                    st.warning("No historical data available for the selected period.")
                
                # Display raw data for debugging
                st.subheader("Raw Data (First 5 rows)")
                st.dataframe(history.head(), use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                
                # Stock Info
                stock_info = [
                    ("Stock Info", "Value"),
                    ("Country", info.get('country', 'N/A')),
                    ("Sector", info.get('sector', 'N/A')),
                    ("Industry", info.get('industry', 'N/A')),
                    ("Market Cap", format_value(info.get('marketCap', 'N/A'))),
                    ("Enterprise Value", format_value(info.get('enterpriseValue', 'N/A'))),
                    ("Employees", info.get('fullTimeEmployees', 'N/A'))
                ]
                df = pd.DataFrame(stock_info[1:], columns=stock_info[0])
                col1.dataframe(df, width=400, hide_index=True)
                
                # Price Info
                price_info = [
                    ("Price Info", "Value"),
                    ("Current Price", f"${info.get('currentPrice', 'N/A'):.2f}"),
                    ("Previous Close", f"${info.get('previousClose', 'N/A'):.2f}"),
                    ("Day High", f"${info.get('dayHigh', 'N/A'):.2f}"),
                    ("Day Low", f"${info.get('dayLow', 'N/A'):.2f}"),
                    ("52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A'):.2f}"),
                    ("52 Week Low", f"${info.get('fiftyTwoWeekLow', 'N/A'):.2f}")
                ]
                df = pd.DataFrame(price_info[1:], columns=price_info[0])
                col2.dataframe(df, width=400, hide_index=True)
                
                # Business Metrics
                biz_metrics = [
                    ("Business Metrics", "Value"),
                    ("EPS (FWD)", f"{info.get('forwardEps', 'N/A'):.2f}"),
                    ("P/E (FWD)", f"{info.get('forwardPE', 'N/A'):.2f}"),
                    ("PEG Ratio", f"{info.get('pegRatio', 'N/A'):.2f}"),
                    ("Div Rate (FWD)", f"${info.get('dividendRate', 'N/A'):.2f}"),
                    ("Div Yield (FWD)", f"{info.get('dividendYield', 'N/A') * 100:.2f}%"),
                    ("Recommendation", info.get('recommendationKey', 'N/A').capitalize())
                ]
                df = pd.DataFrame(biz_metrics[1:], columns=biz_metrics[0])
                col3.dataframe(df, width=400, hide_index=True)
        
        except Exception as e:
            st.exception(f"An error occurred while fetching stock data: {e}")

        st.divider()

        # Stock Racial Harm Data
        st.subheader("Sector Racial Harm Metrics")
        with st.spinner('Fetching sector data...'):
            results = get_sector_data(sector_search)
            
            if not results.empty:
              # Display only the detailed scores, not the full table
                    for index, row in results.iterrows():
                        st.markdown(f"Details for {row['Sector']}:")
        
        # Display Description
        st.markdown(f"**Description:** {row['Description']}")
        
        # Display Primary Subsector and Subsector Weight
        st.markdown(f"**Primary Subsector:** {row['Primary_Subsector']}")
        st.markdown(f"**Subsector Weight:** {row['Subsector_Weight']}")

        # Display metrics in columns
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<h3 style='text-align: center;'>Harm Magnitude</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{row['Harm_Magnitude']}</p>", unsafe_allow_html=True)
        
            st.markdown(f"<h3 style='text-align: center;'>Population Impact</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{row['Population_Impact']}</p>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"<h3 style='text-align: center;'>Directional Movement</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{row['Directional_Movement']}</p>", unsafe_allow_html=True)
        
            st.markdown(f"<h3 style='text-align: center;'>Total Score</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{row['Total_Score']}</p>", unsafe_allow_html=True)
            

            
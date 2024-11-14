import streamlit as st
import sqlite3
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from PIL import Image
import os
from fpdf import FPDF
from io import BytesIO
import tempfile
import datetime
import pytz

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
    margin-top: 0px;
}
.logo {
    height: 100px;
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
    st.image(logo, width=150)

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

def get_unique_values(column_name):
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT DISTINCT {column_name} FROM adasina WHERE {column_name} IS NOT NULL AND {column_name} != ''"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df[column_name].tolist()

def get_response(keyword1, keyword2):
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT Response FROM adasina WHERE Keyword1 = ? AND Keyword2 = ? LIMIT 1
    """
    df = pd.read_sql_query(query, conn, params=(keyword1, keyword2))
    conn.close()
    return df['Response'].iloc[0] if not df.empty else "No matching response found."

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

# Get unique values for dropdowns
subindustries = get_unique_values("Keyword1")
social_justice_screens = get_unique_values("Keyword2")

# Sidebar for user inputs
with st.sidebar:
    st.markdown("<h4 style='font-size: 18px;'>Public Equity Search</h4>", unsafe_allow_html=True)
    ticker = st.text_input("Enter a stock ticker (e.g. MSFT)", "")
    sector_search = st.selectbox("Select industry sector:", [""] + all_sectors)
    period = st.selectbox("Enter a timeframe", ("1D", "5D", "1M", "6M", "YTD", "1Y", "5Y"), index=2)
    
    st.markdown("<h4 style='font-size: 18px;'>Social Justice Screen</h4>", unsafe_allow_html=True)
    subindustry = st.selectbox("Subindustry:", [""] + subindustries)
    social_justice_screen = st.selectbox("Social Justice Screen:", [""] + social_justice_screens)
    
    submit_button = st.button("Search")

# Main content area
st.markdown("<h2 style='font-size: 32px;'>Racial Justice Investment Intelligence Dashboard</h2>", unsafe_allow_html=True)
st.divider()

# Function to create PDF
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add content to the PDF
    pdf.cell(200, 10, txt=f"{ticker} - {info.get('longName', 'N/A')}", ln=1, align='C')
    
    # Add stock price chart
    if not history.empty and 'Close' in history.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=history.index, y=history['Close'], mode='lines', name='Close Price'))
        fig.update_layout(
            title=f'{ticker} Stock Price',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white'
        )
        img_bytes = fig.to_image(format="png")
        
        # Convert bytes to PIL Image
        img = Image.open(BytesIO(img_bytes))
        
        # Save the image to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            img.save(temp_file, format="PNG")
            temp_filename = temp_file.name
        
        # Add the image to the PDF
        pdf.image(temp_filename, x=10, y=30, w=190)
        
        # Remove the temporary file
        os.unlink(temp_filename)
    
    # ... (rest of the function remains the same)

    return pdf.output(dest='S').encode('latin-1')

# Add this new block to display the message when no search has been performed
if not submit_button:
    st.info("Please enter search values in the left sidebar to begin.")

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
        st.subheader("Industry Sector Racial Harm Metrics")
        with st.spinner('Fetching sector data...'):
            results = get_sector_data(sector_search)
            if not results.empty:
                for index, row in results.iterrows():
                    st.markdown(f"Details for {row['Sector']}:")
                    st.markdown(f"**Description:** {row['Description']}")
                    st.markdown(f"**Primary Subsector:** {row['Primary_Subsector']}")
                    st.markdown(f"**Subsector Weight:** {row['Subsector_Weight']}")

                   
                    st.markdown(f"<h3 style='text-align: center;'>Harm Magnitude</h3>", unsafe_allow_html=True)

                    # Function to get Harm-Magnitude content from stockharmdef2
                    def get_harm_magnitude_content(key):
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT \"Harm-Magnitude\" FROM stockharmdef2 WHERE Key = ?", (key,))
                        result = cursor.fetchone()
                        conn.close()
                        if result:
                            return result[0]
                        return "Not found"

                    # Display the integer from the "Harm_Magnitude" column in the "stockracialharm" table
                    harm_magnitude_key = row['Harm_Magnitude']
                    st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{harm_magnitude_key}</p>", unsafe_allow_html=True)

                    # Get and display the content from the "Harm-Magnitude" column in the stockharmdef2 table
                    harm_magnitude_content = get_harm_magnitude_content(harm_magnitude_key)
                    
                    with st.expander("See explanation"):
                        st.write(harm_magnitude_content)


                    st.markdown(f"<h3 style='text-align: center;'>Population Impact</h3>", unsafe_allow_html=True)

                    # Function to get Population Impact content from stockharmdef2
                    def get_pop_impact_content(key):
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT \"Pop-Impact\" FROM stockharmdef2 WHERE Key = ?", (key,))
                        result = cursor.fetchone()
                        conn.close()
                        if result:
                            return result[0]
                        return "Not found"

                    # Display the integer from the "Pop-Impact" column in the "stockracialharm" table
                    pop_impact_key = row['Population_Impact']
                    st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{pop_impact_key}</p>", unsafe_allow_html=True)

                    # Get and display the content from the "Harm-Magnitude" column in the stockharmdef2 table
                    pop_impact_content = get_pop_impact_content(pop_impact_key)
                    
                    with st.expander("See explanation"):
                        st.write(pop_impact_content)    


                    st.markdown(f"<h3 style='text-align: center;'>Directional Movement</h3>", unsafe_allow_html=True)
                    
                    # Function to get Directional Movement content from stockharmdef2
                    def get_directional_trend_content(key):
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT \"Directional-Trend\" FROM stockharmdef2 WHERE Key = ?", (key,))
                        result = cursor.fetchone()
                        conn.close()
                        if result:
                            return result[0]
                        return "Not found"

                    # Display the integer from the "Directional Impact" column in the "stockracialharm" table
                    directional_movement_key = row['Directional_Movement']
                    st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{directional_movement_key}</p>", unsafe_allow_html=True)

                    # Get and display the content from the "Harm-Magnitude" column in the stockharmdef2 table
                    directional_movement_content = get_directional_trend_content(directional_movement_key)
                    
                    with st.expander("See explanation"):
                        st.write(directional_movement_content)  
                    
                    

                    st.markdown(f"<h3 style='text-align: center;'>Total Score</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{row['Total_Score']}</p>", unsafe_allow_html=True)
                    with st.expander("See explanation"):
                        st.write('''
                            The chart above shows some numbers I picked for you.
                            I rolled actual dice for these, so they're *guaranteed* to
                            be random.
                        ''')

        st.divider()

        # New section for Social Justice Screen results
        st.subheader("Social Justice Screen Results")
        if subindustry and social_justice_screen:
            response = get_response(subindustry, social_justice_screen)
            st.write(f"**Subindustry:** {subindustry}")
            st.write(f"**Social Justice Screen:** {social_justice_screen}")
            st.write("**Response:**")
            st.write(response)
        else:
            st.info("Please select both Subindustry and Social Justice Screen to see results.")

        # Add a line space
        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("Key Citations"):
            st.write('''
                The chart above shows some numbers I picked for you.
                I rolled actual dice for these, so they're *guaranteed* to
                be random.
            ''')

        

        def get_future_est_time():
            # Get current time in EST
            est = pytz.timezone('US/Eastern')
            current_time = datetime.datetime.now(est)
            
            # Add 1 hour
            future_time = current_time - datetime.timedelta(hours=1)
            
            # Format the time
            formatted_time = future_time.strftime("%I:%M %p EST")
            
            return formatted_time

        # This will run every time the app is loaded
        future_time = get_future_est_time()

        # Add a line space
        st.markdown("<br>", unsafe_allow_html=True)

        # Generate and provide download button for PDF
        pdf = create_pdf()
        st.download_button(
            label="Download Full Report as PDF",
            data=pdf,
            file_name=f"{ticker}_report.pdf",
            mime="application/pdf"
        )
        # Add a line space
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

         # Display the time
        st.markdown(f"<i>The last update to report data generated at: <b>{future_time}</b></i>", unsafe_allow_html=True)

        with st.expander("Informational Disclaimer"):
            st.write('''
                Reparations Finance Lab and Scatterday & Associates expressly disclaim any liability for financial losses or damages resulting from the use of data or information provided for decision-making purposes. The data and information presented are intended for informational purposes only and should not be construed as financial, investment, or professional advice. Users are advised to conduct their own research and consult with qualified professionals before making any financial or investment decisions. Reparations Finance Lab and Scatterday & Associates make no representations or warranties regarding the accuracy, completeness, or reliability of the data provided. By accessing and using this information, you acknowledge and accept that you do so at your own risk, and that Reparations Finance Lab and Scatterday & Associates shall not be held responsible for any direct, indirect, incidental, consequential, or punitive damages arising from your use of or reliance on the data or information presented.s
            ''')
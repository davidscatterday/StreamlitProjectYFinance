import streamlit as st
import pandas as pd
import sqlite3

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

# Function to get explanation based on harm magnitude
def get_harm_explanation(magnitude):
    conn = sqlite3.connect('DB_PATH)')
    cursor = conn.cursor()
    
    if magnitude == 1:
        column = "Harm-Magnitude-High"
    elif magnitude == 2:
        column = "Harm-Magnitude-Medium"
    elif magnitude == 3:
        column = "Harm-Magnitude-Low"
    else:
        return "No explanation available for this magnitude."

    query = f"SELECT [{column}] FROM stockrhexplanation LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0] if result else "No explanation found."

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
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<h3 style='text-align: center;'>Harm Magnitude</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 24px; font-weight: bold; text-align: center;'>{row['Harm_Magnitude']}</p>", unsafe_allow_html=True)
                
                # Get the explanation based on the harm magnitude
                harm_explanation = get_harm_explanation(row['Harm_Magnitude'])
                
                st.divider()
                st.markdown(f"<p style='text-align: center;'>{harm_explanation}</p>", unsafe_allow_html=True)

                with st.expander("See detailed explanation"):
                    st.write(f"""
                        The Harm Magnitude of {row['Harm_Magnitude']} for the {row['Sector']} sector indicates 
                        the level of potential racial harm associated with this industry. 
                        
                        1 - High Magnitude
                        2 - Medium Magnitude
                        3 - Low Magnitude
                        
                        For more detailed information on how this is calculated and what it means for the 
                        {row['Sector']} sector, please refer to our methodology section.
                    """)
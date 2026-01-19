import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="DP Show Bet Tracker", page_icon="🥧", layout="wide")
DATA_SOURCE = "FULL_LEDGER.csv"

# The Main 6
MAIN_CAST = ["Dan Patrick", "Paulie Pabst", "Todd Fritz", "Seton O'Connor", "Marvin Prince", "Dylan"]

# --- DATA LOADING ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_SOURCE)
        df['Bet Date'] = pd.to_datetime(df['Bet Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Please run the Accountant script.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.title("🥧 Bet Tracker")
selected_person = st.sidebar.radio("Select Personality", ["All"] + MAIN_CAST)

# --- FILTERING ---
if selected_person != "All":
    # Show bets where they are involved in ANY capacity
    view_df = df[
        (df['Proposer'] == selected_person) | 
        (df['Acceptor'] == selected_person) |
        (df['Winner'] == selected_person) |
        (df['Loser'] == selected_person)
    ]
else:
    view_df = df

# --- METRICS ROW ---
st.header("🏆 The Scoreboard")

c1, c2, c3, c4 = st.columns(4)

total_bets = len(view_df)
# Unpaid: They must be the LOSER and status is UNPAID
if selected_person != "All":
    unpaid_count = len(view_df[(view_df['Loser'] == selected_person) & (view_df['Status'] == 'Unpaid')])
    wins = len(view_df[view_df['Winner'] == selected_person])
    losses = len(view_df[view_df['Loser'] == selected_person])
else:
    # Global Unpaid Count
    unpaid_count = len(view_df[view_df['Status'] == 'Unpaid'])
    wins = "N/A"
    losses = "N/A"

c1.metric("Total Bets", total_bets)
c2.metric("Wins", wins)
c3.metric("Losses", losses)
c4.metric("Unpaid Debts", unpaid_count, delta_color="inverse")

# --- MAIN TABLE ---
st.markdown("---")
st.subheader(f"📜 Bet History: {selected_person}")

# Sorting: Unpaid at the top, then by date
view_df = view_df.sort_values(by=["Status", "Bet Date"], ascending=[False, False])

# Clean Table
display_cols = ["Bet Date", "Summary", "Proposer", "Acceptor", "Winner", "Loser", "Status"]

st.dataframe(
    view_df[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Bet Date": st.column_config.DateColumn("Date", format="MM/DD/YYYY"),
        "Summary": st.column_config.TextColumn("Bet Condition", width="large"),
        "Status": st.column_config.Column("Status", width="small"),
        "Winner": st.column_config.Column("Winner", width="medium"),
        "Loser": st.column_config.Column("Loser", width="medium"),
    }
)

# --- SHAME METER CHART ---
if selected_person == "All":
    st.markdown("---")
    st.subheader("🚩 The Wall of Shame (Unpaid Debts by Person)")
    
    # Aggregate Unpaid counts by Loser
    shame_data = df[df['Status'] == 'Unpaid']['Loser'].value_counts().reset_index()
    shame_data.columns = ['Name', 'Unpaid Count']
    
    if not shame_data.empty:
        fig = px.bar(shame_data, x='Name', y='Unpaid Count', color='Name', 
                     title="Who owes the most?")
        st.plotly_chart(fig, use_container_width=True)
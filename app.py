import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    df = pd.read_excel("CDLBO6Stats.xlsx", sheet_name="Sheet1")
    df.columns = df.columns.str.strip()  # Clean column names
    return df

df = load_data()

st.set_page_config(page_title="CDL Player Stat Viewer", layout="wide")
st.title("🧠 CDL Player Stat Viewer")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filters")

    players = sorted(df['player'].dropna().unique())
    selected_player_1 = st.selectbox("Select Player 1", players, index=0)
    selected_player_2 = st.selectbox("Select Player 2", players, index=1)

    opponents = sorted(df['opponent'].dropna().unique())
    selected_opponent = st.selectbox("Select Opponent Faced", opponents)

    all_modes = sorted(df['mode'].dropna().unique())
    selected_mode = st.selectbox("Filter by Mode", ["All"] + all_modes)

    all_majors = sorted(df['major'].dropna().unique())
    selected_major = st.selectbox("Filter by Major", ["All"] + all_majors)

    all_maps = sorted(df['map'].dropna().unique())
    selected_map = st.selectbox("Filter by Map", ["All"] + all_maps)

# Filter function
def apply_filters(data, player):
    filtered = data[data['player'] == player]
    if selected_opponent:
        filtered = filtered[filtered['opponent'] == selected_opponent]
    if selected_mode != "All":
        filtered = filtered[filtered['mode'] == selected_mode]
    if selected_major != "All":
        filtered = filtered[filtered['major'] == selected_major]
    if selected_map != "All":
        filtered = filtered[filtered['map'] == selected_map]
    return filtered

player1_df = apply_filters(df, selected_player_1)
player2_df = apply_filters(df, selected_player_2)

# Display Comparison
st.markdown("## 🆚 Player Comparison")

col1, col2 = st.columns(2)

def display_stats(col, data, player_name):
    col.subheader(f"📊 {player_name}")
    if data.empty:
        col.warning("No data for selected filters.")
        return
    col.dataframe(data[['mode', 'map', 'kills', 'deaths', 'damage', 'W/L']], use_container_width=True)

    wins = data['W/L'].str.lower().eq('w').sum()
    losses = data['W/L'].str.lower().eq('l').sum()
    avg_kills = data['kills'].mean()
    avg_deaths = data['deaths'].mean()
    avg_dmg = data['damage'].mean()
    
    if not data['deaths'].eq(0).all():
        best_map_idx = (data['kills'] / data['deaths']).idxmax()
        best_map = data.loc[best_map_idx, 'map']
    else:
        best_map = "N/A"

    col.markdown(f"""
    - ✅ **Wins:** {wins}
    - ❌ **Losses:** {losses}
    - 🔫 **Avg Kills:** {avg_kills:.2f}
    - 💀 **Avg Deaths:** {avg_deaths:.2f}
    - 💥 **Avg Damage:** {avg_dmg:.0f}
    - 🌍 **Best Map (by K/D):** `{best_map}`
    """)

display_stats(col1, player1_df, selected_player_1)
display_stats(col2, player2_df, selected_player_2)

# 📈 Chart
st.markdown("## 📈 Player 1 Map Performance")
if not player1_df.empty:
    st.line_chart(
        data=player1_df.set_index('map number')[['kills', 'deaths']],
        use_container_width=True
    )

st.markdown("## 📈 Player 2 Map Performance")
if not player2_df.empty:
    st.line_chart(
        data=player2_df.set_index('map number')[['kills', 'deaths']],
        use_container_width=True
    )

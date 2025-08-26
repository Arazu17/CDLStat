import streamlit as st
import pandas as pd
import altair as alt
import sqlite3

# ---------------------------
# Load data from SQLite
# ---------------------------
@st.cache_data
def load_data_from_db():
    conn = sqlite3.connect("CDLBO6StatsDB.db")
    df = pd.read_sql_query("SELECT * FROM cdl_stats", conn)
    conn.close()
    df.columns = df.columns.str.strip()
    return df

df = load_data_from_db()

# ---------------------------
# Page Setup
# ---------------------------
st.set_page_config(page_title="CDL Player Stat Viewer", layout="wide")
st.title("🧠 CDL Player Stat Viewer")

# ---------------------------
# Sidebar Filters
# ---------------------------
with st.sidebar:
    st.header("🔍 Filters")

    players = sorted(df['player'].dropna().unique())
    selected_player_1 = st.selectbox("Select Player 1", players, index=0)
    selected_player_2 = st.selectbox("Select Player 2", players, index=1)

    opponents = ["ALL"] + sorted(df['opponent'].dropna().unique().tolist())
    selected_opponent = st.selectbox("Select Opponent Faced", opponents)

    all_modes = sorted(df['mode'].dropna().unique())
    selected_mode = st.selectbox("Filter by Mode", ["All"] + all_modes)

    all_majors = sorted(df['major'].dropna().unique())
    selected_major = st.selectbox("Filter by Major", ["All"] + all_majors)

    all_maps = sorted(df['map'].dropna().unique())
    selected_map = st.selectbox("Filter by Map", ["All"] + all_maps)

# ---------------------------
# Optional: Insert New Stat & Calculate K/Ds
# ---------------------------
with st.sidebar.expander("➕ Add New Stat"):
    new_mode = st.selectbox("Mode", ["Hardpoint", "Search & Destroy", "Control"])
    new_map = st.text_input("Map")
    new_team = st.text_input("Team")
    new_player = st.text_input("Player")
    new_kills = st.number_input("Kills", min_value=0)
    new_deaths = st.number_input("Deaths", min_value=0)
    new_hill_time = st.number_input("Hill Time", min_value=0)
    new_damage = st.number_input("Damage", min_value=0)
    new_first_blood = st.number_input("First Blood", min_value=0, max_value = 1, step = 1)
    new_major = st.text_input("Major")
    new_type = st.text_input("Type")
    new_opponent = st.text_input("Opponent")
    new_score = st.number_input("Score", min_value=0)
    new_map_number = st.number_input("Map Number", min_value=1)
    new_wl = st.selectbox("W/L", ["W", "L"])

    if st.button("Add Stat"):
        # Calculate series K/D
        series_kd = new_kills / new_deaths if new_deaths != 0 else new_kills
        hardpoint_kd = series_kd if new_mode == "Hardpoint" else 0
        snd_kd = series_kd if new_mode == "Search & Destroy" else 0
        control_kd = series_kd if new_mode == "Control" else 0

        # Insert new row
        conn = sqlite3.connect("CDLBO6StatsDB.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cdl_stats
            (mode,map,team,player,kills,deaths,"hill time",damage,"first blood",major,type,opponent,score,"map number","W/L",
             "series k/d","hardpoint k/d","search & destroy k/d","control k/d","total kills","total deaths",
             "all hardpoint k/d","all search & destroy k/d","all control k/d","overall k/d")
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_mode, new_map, new_team, new_player, new_kills, new_deaths, new_hill_time, new_damage, new_first_blood,
            new_major, new_type, new_opponent, new_score, new_map_number, new_wl,
            series_kd, hardpoint_kd, snd_kd, control_kd, new_kills, new_deaths,
            hardpoint_kd, snd_kd, control_kd, series_kd
        ))
        conn.commit()

        # ---------------------------
        # Update cumulative stats for this player
        # ---------------------------
        player_rows = pd.read_sql_query(f"SELECT * FROM cdl_stats WHERE player='{new_player}'", conn)
        total_kills = player_rows['kills'].sum()
        total_deaths = player_rows['deaths'].sum() if player_rows['deaths'].sum() != 0 else 1

        # Mode-specific totals
        total_hp = player_rows[player_rows['mode'] == 'Hardpoint']['kills'].sum()
        total_hp_deaths = player_rows[player_rows['mode'] == 'Hardpoint']['deaths'].sum() or 1
        total_snd = player_rows[player_rows['mode'] == 'Search & Destroy']['kills'].sum()
        total_snd_deaths = player_rows[player_rows['mode'] == 'Search & Destroy']['deaths'].sum() or 1
        total_control = player_rows[player_rows['mode'] == 'Control']['kills'].sum()
        total_control_deaths = player_rows[player_rows['mode'] == 'Control']['deaths'].sum() or 1

        overall_kd = total_kills / total_deaths
        all_hp_kd = total_hp / total_hp_deaths
        all_snd_kd = total_snd / total_snd_deaths
        all_control_kd = total_control / total_control_deaths

        # Update all rows for this player
        cursor.execute("""
            UPDATE cdl_stats
            SET "total kills"=?, "total deaths"=?, "all hardpoint k/d"=?, "all search & destroy k/d"=?,
                "all control k/d"=?, "overall k/d"=?
            WHERE player=?
        """, (total_kills, total_deaths, all_hp_kd, all_snd_kd, all_control_kd, overall_kd, new_player))
        conn.commit()
        conn.close()

        st.success("✅ New stat added with K/D and cumulative stats updated!")
        df = load_data_from_db()  # Reload data

# ---------------------------
# Filter Function
# ---------------------------
def apply_filters(data, player):
    filtered = data[data['player'] == player]
    if selected_opponent != "ALL":
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

# ---------------------------
# Player Comparison Display
# ---------------------------
st.markdown("## 🆚 Player Comparison")
col1, col2 = st.columns(2)

def display_stats(col, data, player_name):
    col.subheader(f"📊 {player_name}")
    if data.empty:
        col.warning("No data for selected filters.")
        return
    display_columns = ['map', 'opponent', 'W/L', 'kills', 'deaths', 'damage', 'score', 'hill time']
    col.dataframe(data[display_columns], use_container_width=True)

    wins = data['W/L'].str.lower().eq('w').sum()
    losses = data['W/L'].str.lower().eq('l').sum()
    avg_kills = data['kills'].mean()
    avg_deaths = data['deaths'].mean()
    avg_dmg = data['damage'].mean()
    
    best_map = "N/A"
    if not data['deaths'].eq(0).all():
        best_map_idx = (data['kills'] / data['deaths']).idxmax()
        best_map = data.loc[best_map_idx, 'map']

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

# ---------------------------
# Mode-based Bar Graphs
# ---------------------------
def plot_mode_hist(df, player_name):
    modes = ["Hardpoint", "Search & Destroy", "Control"]
    st.markdown(f"## 🎮 {player_name} Mode Performance")

    cols = st.columns(3)
    for mode, col in zip(modes, cols):
        mode_df = df[df["mode"] == mode]

        col.subheader(mode)
        if mode_df.empty:
            col.warning(f"No {mode} data.")
            continue

        kills_count = mode_df["kills"].value_counts().reset_index()
        kills_count.columns = ["kills", "frequency"]
        kills_count = kills_count.sort_values("kills")
        kills_count["kills"] = kills_count["kills"].astype(int)
        kills_count["frequency"] = kills_count["frequency"].astype(int)

        chart = (
            alt.Chart(kills_count)
            .mark_bar()
            .encode(
                x=alt.X("kills:O", title="Kills"),
                y=alt.Y("frequency:Q", title="Frequency"),
                tooltip=["kills", "frequency"]
            )
        )
        col.altair_chart(chart, use_container_width=True)

if not player1_df.empty:
    plot_mode_hist(player1_df, selected_player_1)
if not player2_df.empty:
    plot_mode_hist(player2_df, selected_player_2)

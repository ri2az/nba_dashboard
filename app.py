import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pydeck as pdk

# --- PAGE CONFIG ---
st.set_page_config(page_title="NBA Dashboard", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("📅 Paramètres")
season = st.sidebar.selectbox("Saison NBA", list(range(2025, 2019, -1)))
st.sidebar.markdown("---")

# --- SCRAPE STANDINGS ---
@st.cache_data
def scrape_standings(season):
    url = f"https://www.basketball-reference.com/leagues/NBA_{season}_standings.html"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    tables = {
        "Eastern Conference": soup.find("table", {"id": "confs_standings_E"}),
        "Western Conference": soup.find("table", {"id": "confs_standings_W"}),
    }
    data = []
    for conf, table in tables.items():
        df = pd.read_html(str(table))[0]
        df.columns.values[0] = "Team"
        df["Conference"] = conf
        data.append(df)
    df = pd.concat(data, ignore_index=True)
    df["Team"] = df["Team"].str.replace(r"\\*", "", regex=True).str.strip()
    df["Division"] = df["Team"].str.extract(r"\\((.*?)\\)")[0]
    df["Team"] = df["Team"].str.replace(r"\\(.*\\)", "", regex=True).str.strip()
    df = df.rename(columns={
        "W": "Wins", "L": "Losses", "W/L%": "Win%",
        "GB": "Games Behind", "PS/G": "Points For", "PA/G": "Points Against"
    })
    df["Point Diff"] = df["Points For"] - df["Points Against"]
    return df

# --- SCRAPE UPCOMING GAMES ---
@st.cache_data
def get_upcoming_games():
    url = "https://www.espn.com/nba/schedule"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    games = []
    for table in soup.find_all("table", class_="ScheduleTable"):
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                teams = cols[0].text.strip()
                time = cols[1].text.strip()
                tv = cols[2].text.strip()
                games.append({"Match": teams, "Heure": time, "TV": tv})
    return pd.DataFrame(games)

# --- SCRAPE PLAYER STATS ---
@st.cache_data
def get_player_stats(season):
    url = f"https://www.basketball-reference.com/leagues/NBA_{season}_per_game.html"
    res = requests.get(url)
    dfs = pd.read_html(res.text)
    df_stats = dfs[0]
    df_stats = df_stats[df_stats.Player != "Player"]
    df_stats = df_stats.dropna(subset=["PTS", "AST", "TRB"])
    df_stats[["PTS", "AST", "TRB"]] = df_stats[["PTS", "AST", "TRB"]].astype(float)
    return df_stats

# --- NBA TEAMS GEO DATA WITH LOGOS ---
nba_teams = [
    {"team": "Atlanta Hawks", "latitude": 33.7573, "longitude": -84.3963,
     "logo_url": "https://loodibee.com/wp-content/uploads/nba-atlanta-hawks-logo.png"},
    {"team": "Boston Celtics", "latitude": 42.3662, "longitude": -71.0621,
     "logo_url": "https://loodibee.com/wp-content/uploads/nba-boston-celtics-logo.png"},
]
df_teams_geo = pd.DataFrame(nba_teams)
df_teams_geo["icon_data"] = df_teams_geo.apply(lambda row: {
    "url": row["logo_url"], "width": 128, "height": 128, "anchorY": 128
}, axis=1)

icon_layer = pdk.Layer(
    type="IconLayer",
    data=df_teams_geo,
    get_icon="icon_data",
    get_size=50000,
    size_scale=1,
    get_position=["longitude", "latitude"],
    pickable=True
)
view_state = pdk.ViewState(latitude=37.0902, longitude=-95.7129, zoom=4, pitch=0)
deck_map = pdk.Deck(layers=[icon_layer], initial_view_state=view_state, tooltip={"text": "{team}"})

# --- LOAD DATA ---
df = scrape_standings(season)
player_stats = get_player_stats(season)

# --- FILTERS ---
st.sidebar.header("Filtres de classement")
selected_conf = st.sidebar.multiselect("Conférences", df["Conference"].unique(), default=list(df["Conference"].unique()))
selected_div = st.sidebar.multiselect("Divisions", df["Division"].dropna().unique(), default=list(df["Division"].dropna().unique()))
team_search = st.sidebar.text_input("🔍 Rechercher une équipe")
filter_mode = st.sidebar.radio("Tri rapide", ["Aucun", "Top 5 (Win%)", "Bottom 5 (Win%)"])

# --- APPLY FILTERS ---
filtered_df = df[df["Conference"].isin(selected_conf)]
if selected_div:
    filtered_df = filtered_df[filtered_df["Division"].isin(selected_div)]
if team_search:
    filtered_df = filtered_df[filtered_df["Team"].str.contains(team_search, case=False)]
if filter_mode == "Top 5 (Win%)":
    filtered_df = filtered_df.sort_values(by="Win%", ascending=False).head(5)
elif filter_mode == "Bottom 5 (Win%)":
    filtered_df = filtered_df.sort_values(by="Win%", ascending=True).head(5)

# --- DISPLAY ---
st.title(f"\U0001F3C0 NBA {season} - Dashboard interactif")

# --- LEADERS ---
st.subheader("\U0001F3C6 Leaders par statistique")
col1, col2, col3 = st.columns(3)
with col1:
    top_wins = df.sort_values(by="Wins", ascending=False).iloc[0]
    st.metric("+Victoires", top_wins["Team"], f'{int(top_wins["Wins"])}')
with col2:
    top_win_pct = df.sort_values(by="Win%", ascending=False).iloc[0]
    st.metric("+% Victoires", top_win_pct["Team"], f'{top_win_pct["Win%"]:.3f}')
with col3:
    top_diff = df.sort_values(by="Point Diff", ascending=False).iloc[0]
    st.metric("+Diff. Points", top_diff["Team"], f'{top_diff["Point Diff"]:.1f}')

# --- CLASSEMENT ---
sort_col = st.selectbox("Trier par", ["Wins", "Losses", "Win%", "Point Diff"])
filtered_df = filtered_df.sort_values(by=sort_col, ascending=False)
st.subheader("\U0001F4CB Classement NBA")
st.dataframe(filtered_df[["Team", "Conference", "Division", "Wins", "Losses", "Win%", "Point Diff"]].reset_index(drop=True).style.format({"Win%": "{:.3f}", "Point Diff": "{:.1f}"}), use_container_width=True)

# --- EXPORT ---
st.download_button("📂 Exporter en CSV", filtered_df.to_csv(index=False), file_name=f"classement_nba_{season}.csv")

# --- GRAPHS ---
st.subheader("\U0001F4CA Graphiques")
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.bar(filtered_df["Team"], filtered_df["Wins"], color="#1f77b4")
ax1.set_ylabel("Victoires")
ax1.set_title("Nombre de victoires par équipe")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig1)

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.plot(filtered_df["Team"], filtered_df["Win%"], marker="o", color="#ff7f0e")
ax2.set_ylabel("Win%")
ax2.set_title("Pourcentage de victoires par équipe")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig2)

fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.bar(filtered_df["Team"], filtered_df["Point Diff"], color="green")
ax3.axhline(0, color="gray", linestyle="--")
ax3.set_ylabel("Diff. Points")
ax3.set_title("Différentiel de points par équipe")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
st.pyplot(fig3)

# --- PLAYOFF TRACKER ---
st.subheader("🏆 Simu playoffs - Top 8 par conférence")
col_est, col_ouest = st.columns(2)

# Style tableau lisible
table_styles = [
    {'selector': 'th', 'props': [('text-align', 'center'), ('font-size', '14px')]},
    {'selector': 'td', 'props': [('text-align', 'center'), ('white-space', 'nowrap')]}
]

with col_est:
    st.markdown("### 🔹 Est")
    top_east = df[df["Conference"] == "Eastern Conference"].sort_values(by="Win%", ascending=False).head(8)
    top_east = top_east[["Team", "Wins", "Losses", "Win%", "Point Diff"]].reset_index(drop=True)
    styled_east = top_east.style\
        .format({"Win%": "{:.3f}", "Point Diff": "{:+.1f}"})\
        .set_table_styles(table_styles)
    st.dataframe(styled_east, use_container_width=False, height=350)

with col_ouest:
    st.markdown("### 🔸 Ouest")
    top_west = df[df["Conference"] == "Western Conference"].sort_values(by="Win%", ascending=False).head(8)
    top_west = top_west[["Team", "Wins", "Losses", "Win%", "Point Diff"]].reset_index(drop=True)
    styled_west = top_west.style\
        .format({"Win%": "{:.3f}", "Point Diff": "{:+.1f}"})\
        .set_table_styles(table_styles)
    st.dataframe(styled_west, use_container_width=False, height=350)

# --- MATCHS À VENIR ---
st.subheader("\U0001F4C5 Matchs à venir (aujourd’hui)")
games_df = get_upcoming_games()
if not games_df.empty:
    st.dataframe(games_df, use_container_width=True)
else:
    st.info("Aucun match trouvé pour aujourd’hui.")

# --- JOUEURS ---
st.subheader("\U0001F3C3‍ Top joueurs par stat (par match)")
st.markdown("**Top 10 Pointeurs**")
st.dataframe(player_stats.sort_values(by="PTS", ascending=False)[["Player", "PTS"]].head(10), use_container_width=True)
st.markdown("**Top 10 Passeurs**")
st.dataframe(player_stats.sort_values(by="AST", ascending=False)[["Player", "AST"]].head(10), use_container_width=True)
st.markdown("**Top 10 Rebondeurs**")
st.dataframe(player_stats.sort_values(by="TRB", ascending=False)[["Player", "TRB"]].head(10), use_container_width=True)

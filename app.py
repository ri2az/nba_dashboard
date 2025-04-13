import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import pydeck as pdk
import seaborn as sns
import numpy as np
import matplotlib.patches as patches
import random


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

# --- MVP / IMPACT ---
st.subheader("🏅 Classement MVP / Impact")

# --- Paramètres depuis la sidebar ---
st.sidebar.header("⚙️ Poids MVP")
coef_pts = st.sidebar.slider("Poids des Points (PTS)", 0.0, 2.0, 0.5, 0.1)
coef_ast = st.sidebar.slider("Poids des Passes (AST)", 0.0, 2.0, 1.2, 0.1)
coef_trb = st.sidebar.slider("Poids des Rebonds (TRB)", 0.0, 2.0, 1.0, 0.1)

# --- Filtrage : minimum 65 matchs joués ---
player_stats_filtered = player_stats[player_stats["G"] >= 65]

# --- Calcul de l'impact personnalisé ---
player_stats_filtered["Impact Score"] = (
    player_stats_filtered["PTS"] * coef_pts +
    player_stats_filtered["AST"] * coef_ast +
    player_stats_filtered["TRB"] * coef_trb
)

top_impact = player_stats_filtered.sort_values(by="Impact Score", ascending=False)[
    ["Player", "G", "PTS", "AST", "TRB", "Impact Score"]
].head(10)

top_impact["Impact Score"] = top_impact["Impact Score"].round(2)

st.markdown("**Top 10 joueurs par score d'impact personnalisé (≥ 65 matchs joués)**")
st.dataframe(top_impact.reset_index(drop=True), use_container_width=True)

# --- HEATMAP JOUEUR ---
st.subheader("🌡️ Heatmap de stats par joueur")

# Liste déroulante avec noms de joueurs
player_names = player_stats["Player"].unique()
selected_player = st.selectbox("Sélectionner un joueur", sorted(player_names))

# Sélection des colonnes à visualiser
heatmap_stats = ["PTS", "AST", "TRB", "STL", "BLK", "TOV", "FG%", "3P%", "FT%"]
available_stats = [stat for stat in heatmap_stats if stat in player_stats.columns]

# Récupération des stats du joueur sélectionné
player_row = player_stats[player_stats["Player"] == selected_player].iloc[0]
player_data = player_row[available_stats].astype(float)

# Création d’un DataFrame 2D pour la heatmap
heatmap_df = pd.DataFrame(player_data.values.reshape(1, -1), columns=available_stats, index=[selected_player])

# Création de la heatmap
fig, ax = plt.subplots(figsize=(10, 1.5))
sns.heatmap(heatmap_df, annot=True, cmap="coolwarm", cbar=False, fmt=".2f", linewidths=1, linecolor="white", ax=ax)
ax.set_title(f"Heatmap des stats de {selected_player}", fontsize=12)
st.pyplot(fig)

# --- STATS GÉNÉRALES DES JOUEURS ---
st.subheader("📊 Statistiques générales des joueurs")

# Vérifie les colonnes disponibles
stat_cols = ["Player", "Pos", "Team", "G", "MP", "PTS", "AST", "TRB", "STL", "BLK", "TOV", "FG%", "3P%", "FT%"]
available_cols = [col for col in stat_cols if col in player_stats.columns]

# --- FILTRES ---
st.markdown("### 🎛️ Filtres")

# Recherche par nom
search_player = st.text_input("🔍 Rechercher un joueur")

# Filtre équipe
teams = sorted(player_stats["Team"].dropna().unique())
selected_teams = st.multiselect("🧢 Équipes", options=teams, default=teams)

# Filtre par position (si disponible)
if "Pos" in player_stats.columns:
    positions = sorted(player_stats["Pos"].dropna().unique())
    selected_positions = st.multiselect("📌 Postes", options=positions, default=positions)
else:
    selected_positions = None

# --- APPLICATION DES FILTRES ---
filtered_players = player_stats.copy()
if search_player:
    filtered_players = filtered_players[filtered_players["Player"].str.contains(search_player, case=False)]
if selected_teams:
    filtered_players = filtered_players[filtered_players["Team"].isin(selected_teams)]
if selected_positions:
    filtered_players = filtered_players[filtered_players["Pos"].isin(selected_positions)]

# --- AFFICHAGE + EXPORT ---
st.dataframe(filtered_players[available_cols].reset_index(drop=True), use_container_width=True)

csv_export = filtered_players[available_cols].to_csv(index=False)
st.download_button("📥 Télécharger en CSV", data=csv_export, file_name=f"stats_joueurs_{season}_filtrées.csv", mime="text/csv")

    # --- Fonction utilitaire pour simuler un round ---
def simulate_round(matchups, simulate):
    winners = []
    for i, (team1, team2) in enumerate(matchups, start=1):
        if simulate:
            winner = simulate_game(team1, team2)
            st.write(f"Match {i} : **{team1['Team']}** vs **{team2['Team']}** → 🏅 **{winner}**")
        else:
            winner = st.radio(f"Match {i} : {team1['Team']} vs {team2['Team']}",
                              options=[team1["Team"], team2["Team"]], key=f"r{random.random()}")
        winners.append(winner)
    return winners

    st.subheader("🏆 Simulation complète des Playoffs")

# 1. Création des matchs de 1er tour
def create_matchups(df_top8):
    return [(df_top8.iloc[i], df_top8.iloc[7 - i]) for i in range(4)]

top8_east = df[df["Conference"] == "Eastern Conference"].sort_values(by="Win%", ascending=False).head(8).reset_index(drop=True)
top8_west = df[df["Conference"] == "Western Conference"].sort_values(by="Win%", ascending=False).head(8).reset_index(drop=True)

matchups_east = create_matchups(top8_east)
matchups_west = create_matchups(top8_west)

simulate_button = st.button("🎲 Simuler les playoffs automatiquement")

# 2. Premier tour
st.markdown("### 🔹 1er Tour Est")
east_qf = simulate_round(matchups_east, simulate=simulate_button)

st.markdown("### 🔸 1er Tour Ouest")
west_qf = simulate_round(matchups_west, simulate=simulate_button)

# 3. Demi-finales
def get_team_row(team_name):
    return df[df["Team"] == team_name].iloc[0]

st.markdown("### 🔹 Demi-finales Est")
east_sf_matchups = [(get_team_row(east_qf[0]), get_team_row(east_qf[3])),
                    (get_team_row(east_qf[1]), get_team_row(east_qf[2]))]
east_sf = simulate_round(east_sf_matchups, simulate=simulate_button)

st.markdown("### 🔸 Demi-finales Ouest")
west_sf_matchups = [(get_team_row(west_qf[0]), get_team_row(west_qf[3])),
                    (get_team_row(west_qf[1]), get_team_row(west_qf[2]))]
west_sf = simulate_round(west_sf_matchups, simulate=simulate_button)

# 4. Finales de Conférence
st.markdown("### 🔹 Finale Est")
east_final = simulate_round([(get_team_row(east_sf[0]), get_team_row(east_sf[1]))], simulate=simulate_button)
champion_est = east_final[0]

st.markdown("### 🔸 Finale Ouest")
west_final = simulate_round([(get_team_row(west_sf[0]), get_team_row(west_sf[1]))], simulate=simulate_button)
champion_west = west_final[0]

# 5. Finale NBA
st.markdown("## 🏆 Finale NBA")
nba_final = simulate_round([(get_team_row(champion_est), get_team_row(champion_west))], simulate=simulate_button)
champion_nba = nba_final[0]

# 6. Résultat
st.success(f"🥇 **Champion NBA simulé : {champion_nba}** 🎉")

def draw_bracket(east_teams, west_teams, east_sf, west_sf, champ_east, champ_west, champ_nba):
    fig, ax = plt.subplots(figsize=(12, 7))
    
    def draw_side(start_x, teams, sf, champ, label):
        y_positions = [6, 4.5, 3, 1.5]
        # 1er tour
        for i, team in enumerate(teams):
            ax.text(start_x, y_positions[i], team, va='center', fontsize=9, bbox=dict(boxstyle="round", fc="lightblue"))
            ax.plot([start_x + 0.5, start_x + 1], [y_positions[i]] * 2, color='black')

        # Demi-finales
        sf_positions = [5.25, 2.25]
        for i, team in enumerate(sf):
            ax.text(start_x + 1.5, sf_positions[i], team, va='center', fontsize=9, bbox=dict(boxstyle="round", fc="skyblue"))
            ax.plot([start_x + 1, start_x + 1.5], [y_positions[i], sf_positions[i]], color='black')
            ax.plot([start_x + 1, start_x + 1.5], [y_positions[3 - i], sf_positions[i]], color='black')

        # Finale de conf
        ax.text(start_x + 3, 3.75, champ, va='center', fontsize=10, weight='bold',
                bbox=dict(boxstyle="round", fc="deepskyblue"))
        ax.plot([start_x + 1.5, start_x + 3], [sf_positions[0], 3.75], color='black')
        ax.plot([start_x + 1.5, start_x + 3], [sf_positions[1], 3.75], color='black')

        # Lien vers finale NBA
        return 3.75

    y_east = draw_side(0.5, east_teams, east_sf, champ_east, "EST")
    y_west = draw_side(8.5, west_teams, west_sf, champ_west, "OUEST")

    # Finale NBA
    ax.text(5.5, 3.75, champ_nba, va='center', ha='center', fontsize=11,
            bbox=dict(boxstyle="round", fc="gold"))
    ax.plot([3.5, 5.5], [y_east, 3.75], color='black')
    ax.plot([9.5, 5.5], [y_west, 3.75], color='black')

    ax.axis("off")
    ax.set_title("🏆 Bracket des Playoffs NBA", fontsize=14)
    st.pyplot(fig)

    # --- Fonction de simulation d'un match basée sur le Win% ---
def simulate_game(team1, team2):
    prob_team1 = team1["Win%"] / (team1["Win%"] + team2["Win%"])
    return team1["Team"] if random.random() < prob_team1 else team2["Team"]

def draw_bracket(east_teams, west_teams, east_sf, west_sf, champ_east, champ_west, champ_nba):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(16, 9))

    def draw_side(start_x, teams, sf, champ, align='left'):
        # Positions Y pour chaque niveau
        y_qf = [7.5, 5.5, 3.5, 1.5]  # 1er tour
        y_sf = [(y_qf[0] + y_qf[1]) / 2, (y_qf[2] + y_qf[3]) / 2]  # demi
        y_final = (y_sf[0] + y_sf[1]) / 2  # finale conf

        # Draw QF
        for i, team in enumerate(teams):
            ax.text(start_x, y_qf[i], team, fontsize=9, va='center',
                    ha=align, bbox=dict(boxstyle="round", fc="lightblue"))
            offset = 0.5 if align == 'left' else -0.5
            ax.plot([start_x, start_x + offset], [y_qf[i], y_qf[i]], color='black')

        # Draw SF
        for i, team in enumerate(sf):
            ax.text(start_x + offset + (0.5 if align == 'left' else -0.5),
                    y_sf[i], team, fontsize=9, va='center',
                    ha=align, bbox=dict(boxstyle="round", fc="skyblue"))
            # Connexions
            ax.plot([start_x + offset, start_x + offset + (0.5 if align == 'left' else -0.5)],
                    [y_qf[2 * i], y_sf[i]], color='black')
            ax.plot([start_x + offset, start_x + offset + (0.5 if align == 'left' else -0.5)],
                    [y_qf[2 * i + 1], y_sf[i]], color='black')

        # Draw Final Conf
        ax.text(start_x + (2 if align == 'left' else -2), y_final,
                champ, fontsize=10, weight='bold',
                ha='center', va='center', bbox=dict(boxstyle="round", fc="deepskyblue"))

        # Lignes jusqu'à la finale conf
        ax.plot([start_x + offset + (0.5 if align == 'left' else -0.5),
                 start_x + (2 if align == 'left' else -2)],
                [y_sf[0], y_final], color='black')
        ax.plot([start_x + offset + (0.5 if align == 'left' else -0.5),
                 start_x + (2 if align == 'left' else -2)],
                [y_sf[1], y_final], color='black')

        return y_final

    # Côté Est à gauche
    y_east = draw_side(0.5, east_teams, east_sf, champ_east, align='left')

    # Côté Ouest à droite
    y_west = draw_side(15.5, west_teams, west_sf, champ_west, align='right')

    # Finale NBA au centre
    ax.text(8, 4.5, champ_nba, fontsize=11, va='center', ha='center',
            bbox=dict(boxstyle="round", fc="gold"))
    ax.plot([2.5, 8], [y_east, 4.5], color='black')
    ax.plot([13.5, 8], [y_west, 4.5], color='black')

    # Titre
    ax.set_title("🏀 Bracket des Playoffs NBA", fontsize=16, pad=20)

    # Nettoyage
    ax.axis('off')
    st.pyplot(fig)

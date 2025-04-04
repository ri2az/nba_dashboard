# 🏀 NBA Dashboard - Saison en direct

Bienvenue dans ce tableau de bord interactif NBA développé avec **Streamlit** !  
Il permet de suivre les performances des équipes, les stats des joueurs, les classements par conférence/division, les matchs à venir, et plus encore.

---

## 🔧 Fonctionnalités

- 📊 Classement NBA en temps réel (données de [basketball-reference.com](https://www.basketball-reference.com))
- 🏆 Simulateur Playoffs : Top 8 Est & Ouest
- 📺 Affichage des matchs à venir (données de [ESPN](https://www.espn.com/nba/schedule))
- 🧠 Filtres dynamiques (conférences, divisions, tri, recherche)
- 🧍 Stats joueurs (points, passes, rebonds)
- 📥 Export CSV du classement
- 🖼️ Logos des équipes dans le classement

---

## 📦 Librairies utilisées

- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Requests](https://docs.python-requests.org/en/latest/)

---

## ▶️ Lancer l'application

Assurez-vous d'avoir **Python 3.8+** installé.

```bash
# Crée un environnement virtuel (optionnel mais recommandé)
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sur Windows

# Installe les dépendances
pip install -r requirements.txt

# Lance Streamlit
streamlit run app.py

# 🏀 NBA Dashboard - Saison en direct

Bienvenue dans ce tableau de bord interactif NBA développé avec **Streamlit** !  
Il permet de suivre les performances des équipes, les stats des joueurs, les classements par conférence/division, les matchs à venir, et plus encore.

---

## 🔧 Fonctionnalités

- 📊 Visualiser les classements NBA par saison
- 🧠 Explorer les leaders statistiques (victoires, Win%, différentiel de points)
- 🎮 Simuler les playoffs et afficher le bracket
- 🏅 Générer un classement MVP personnalisé basé sur les performances
- 🔥 Afficher une heatmap des statistiques d’un joueur
- 📆 Voir les matchs à venir
- 📥 Exporter les données en CSV

---

## 📦 Librairies utilisées

- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Requests](https://docs.python-requests.org/en/latest/)

---

### 4️⃣ Lancer l'application sur Streamlit !

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://riaaznba.streamlit.app/)

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

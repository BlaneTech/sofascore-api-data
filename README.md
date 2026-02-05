# GOGAinde-Data

Plateforme de collecte et d'analyse de données pour la Coupe d'Afrique des Nations (CAN).

## Structure du Projet

```
GOGAinde-Data/
├── .venv/                  # Environnement virtuel Python
├── app/                    # Code principal de l'application
│   ├── api/                # Endpoints et routes API
│   ├── core/               # Configuration et constantes
│   │   └── config.py       # Configuration centralisée
│   ├── db/                 # Gestion de la base de données
│   │   ├── database.py     # Configuration SQLAlchemy
│   │   └── models.py       # Modèles de données
│   ├── schemas/            # Schémas Pydantic / validation
│   ├── services/           # Logique métier
│   │   └── scraper/        # Services de scraping Sofascore
│   │       ├── league_service.py
│   │       ├── team_service.py
│   │       ├── fixture_service.py
│   │       ├── lineup_service.py
│   │       ├── statistics_service.py
│   │       └── cup_tree_service.py
│   ├── utils/              # Fonctions utilitaires
│   │   └── db_helpers.py
│   └── main.py             # Point d'entrée de l'application
├── docker/                 # Fichiers liés à Docker
├── notebooks/              # Jupyter notebooks / analyses
├── pipeline/               # Scripts de pipeline
│   └── ingest_afcon.py     # Script d'ingestion AFCON
├── tests/                  # Tests unitaires et d'intégration
├── .env                    # Variables d'environnement
├── .env.example            # Exemple de variables d'environnement
├── .gitignore              # Fichiers ignorés par Git
├── docker-compose.yml      # Configuration Docker Compose
├── Makefile                # Commandes automatisées
├── README.md               # Documentation du projet
└── requirements.txt        # Dépendances Python
```

## Installation

### 1. Cloner le repository

```bash
git clone <repo-url>
cd GOGAinde-Data
```

### 2. Créer l'environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

### 3. Installer les dépendances

```bash
make install
# ou
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copier le fichier .env.example
cp .env.example .env

# Éditer .env avec vos paramètres
nano .env
```

### 5. Initialiser la base de données

```bash
make db-init
```

## Base de Données

### Modèles disponibles

- **League** : Compétitions (CAN, qualifications, etc.)
- **Season** : Saisons par compétition
- **Team** : Équipes nationales
- **Manager** : Entraîneurs 
- **TeamManager** : Historique entraîneurs par équipe 
- **Player** : Joueurs
- **Fixture** : Matchs
- **MatchEvent** : Événements de match (buts, cartons, etc.)
- **Lineup** : Compositions d'équipe
- **MatchStatistics** : Statistiques de match (avec contrainte unique)
- **PlayerStatistics** : Statistiques joueur
- **TeamStatistics** : Statistiques équipe
- **Standing** : Classements

##  Utilisation

### Lancer le scraping AFCON

```bash
# Via Makefile
make scrape-afcon

# Ou directement
python pipeline/ingest_afcon.py
```

### Lancer l'API

```bash
make dev
# L'API sera disponible sur http://localhost:8000
# Documentation: http://localhost:8000/docs
```

### Lancer les tests

```bash
make test
```

### Lancer Jupyter

```bash
make notebook
```

##  Docker

### Lancer avec Docker Compose

```bash
make docker-up
```

### Voir les logs

```bash
make docker-logs
```

### Arrêter les conteneurs

```bash
make docker-down
```

##  Commandes Make Disponibles

```bash
make help              # Affiche l'aide
make install           # Installe les dépendances
make dev               # Lance l'application en mode dev
make test              # Lance les tests
make clean             # Nettoie les fichiers temporaires
make db-init           # Initialise la base de données
make db-migrate        # Lance les migrations Alembic
make scrape-afcon      # Lance le scraping AFCON
make docker-up         # Lance les conteneurs Docker
make docker-down       # Arrête les conteneurs Docker
make docker-logs       # Affiche les logs Docker
make notebook          # Lance Jupyter
```


### Services de Scraping

Les services de scraping sont organisés par responsabilité :

- **league_service** : Gestion des leagues et seasons
- **team_service** : Gestion des équipes et joueurs
- **fixture_service** : Gestion des matchs
- **lineup_service** : Gestion des compositions
- **statistics_service** : Gestion des statistiques
- **cup_tree_service** : Gestion des phases finales

### Flux d'ingestion

```
1. Recherche compétition AFCON
2. Récupération saisons et rounds
3. Pour chaque round:
   - Ingestion league/season
   - Ingestion équipes
   - Ingestion joueurs
   - Ingestion matchs
   - Ingestion lineups
   - Ingestion statistiques
4. Ingestion phases finales (cup tree)
```

## Auteurs

ACCEL-TECH
www.accel-tech.net

---

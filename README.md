# GOGAinde-Data

## Structure du Projet 
 
``` 
gogainde-data/ 
├── API_RECAP.md                        # Récapitulatif des endpoints et API disponibles
├── Makefile                            # Commandes automatisées pour build/test/deploiement
├── README.md                           # Documentation principale du projet
├── __init__.py                         # Indique que le dossier est un package Python
├── app/                                # Code principal de l'application
│   ├── api/                            # Endpoints et routes API (FastAPI)
│   │   ├── events.py                   # Endpoints pour les événements de match
│   │   ├── fixtures.py                 # Endpoints pour les matchs programmés
│   │   ├── leagues.py                  # Endpoints pour les ligues
│   │   ├── lineups.py                  # Endpoints pour les compositions d’équipes
│   │   ├── managers.py                 # Endpoints pour les entraîneurs
│   │   ├── players.py                  # Endpoints pour les joueurs
│   │   ├── seasons.py                  # Endpoints pour les saisons
│   │   ├── standings.py                # Endpoints pour les classements
│   │   ├── statistics.py               # Endpoints pour les statistiques
│   │   └── teams.py                    # Endpoints pour les équipes
│   ├── core/                           # Configuration et constantes
│   │   └── config.py                   # Paramètres centralisés (env, DB, etc.)
│   ├── db/                             # Gestion de la base de données
│   │   ├── MODELS_DOCUMENTATION.md     # Documentation des modèles SQLAlchemy
│   │   ├── database.py                 # Connexion et configuration SQLAlchemy
│   │   ├── init_db.py                  # Initialisation et création des tables
│   │   ├── models.py                   # Définition des modèles ORM
│   │   └── session.py                  # Gestion des sessions DB
│   ├── main.py                         # Point d’entrée de l’application (FastAPI)
│   ├── schemas/                        # Schémas Pydantic pour validation
│   │   └── base.py                     # Schémas de base communs
│   ├── services/                       # Logique métier
│   │   └── scraper/                    # Services de scraping (Sofascore, etc.)
│   │       ├── cup_tree_service.py     # Scraping arbre de coupe
│   │       ├── fixture_service.py      # Scraping des matchs
│   │       ├── league_service.py       # Scraping des ligues
│   │       ├── lineup_service.py       # Scraping des compositions
│   │       ├── manager_service.py      # Scraping des entraîneurs
│   │       ├── match_event_service.py  # Scraping des événements de match
│   │       ├── standing_service.py     # Scraping des classements
│   │       ├── statistics_service.py   # Scraping des statistiques
│   │       └── team_service.py         # Scraping des équipes
│   └── utils/                          # Fonctions utilitaires
│       └── db_helpers.py               # Helpers pour interactions DB
├── docker/                             # Fichiers liés à Docker
│   ├── Dockerfile                      # Image Docker de l’application
│   └── nginx.conf                      # Configuration Nginx
├── docker-compose.yml                  # Orchestration multi-services Docker
├── pipeline/                           # Scripts de pipeline de données
│   └── ingest_afcon.py                 # Script d’ingestion des données
├── requirements.txt                    # Dépendances Python
└── tests/                              # Tests unitaires et d’intégration
    └── test_api.py                     # Tests des endpoints API
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

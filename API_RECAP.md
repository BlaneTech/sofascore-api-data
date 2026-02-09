# API GOGAINDE-DATA - SYNTHÈSE COMPLÈTE

---

### Schémas Pydantic
```
app/schemas/
├── base.py             Tous les schémas
└── __init__.py

Schémas:
- TeamBase, TeamDetailed
- LeagueBase, SeasonBase
- PlayerBase, PlayerDetailed
- FixtureBase, FixtureDetailed
- MatchEventSchema
- LineupSchema, LineupPlayerSchema
- MatchStatisticsSchema
- StandingSchema
- APIResponse, PaginationMeta
- FixtureFilters, TeamFilters, PlayerFilters
```

###  API Endpoints
```
app/api/
├── __init__.py
├── events.py           5 endpoints
├── fixtures.py         7 endpoints
├── leagues.py          3 endpoints
├── lineups.py          5 endpoints
├── managers.py         2 endpoints
├── players.py          6 endpoints
├── seasons.py          5 endpoints
├── standings.py        2 endpoints
├── statistics.py       4 endpoints
└── teams.py            4 endpoints

Total: 44 endpoints
```



###  Application
```
app/
├── main.py             FastAPI app principale
└── ...
```

### Documentation & Tests
```
├── API_DOCUMENTATION.md     Doc complète
├── tests/
│   ├── __init__.py
│   └── test_api.py     10 tests
```

---

##  ENDPOINTS DISPONIBLES

###  Leagues (3 endpoints)
```
GET  /leagues                     # Liste des leagues
GET  /leagues/{id}                # Détail league
GET  /leagues/{id}/seasons        # Saisons d'une league
```

###  Teams (4 endpoints)
```
GET  /teams                       # Liste des équipes
GET  /teams/{id}                  # Détail équipe
GET  /teams/{id}/players          # Joueurs d'une équipe
GET  /teams/{id}/statistics       # Stats équipe
```

###  Fixtures (7 endpoints)
```
GET  /fixtures                    # Liste des matchs
GET  /fixtures/{id}               # Détail match
GET  /fixtures/{id}/events        # Événements (buts, cartons)
GET  /fixtures/{id}/lineups       # Compositions
GET  /fixtures/{id}/statistics    # Statistiques match
GET  /fixtures/live/all           # Matchs en cours
```

###  Players (3 endpoints)
```
GET  /players                     # Liste des joueurs
GET  /players/{id}                # Détail joueur
GET  /players/{id}/statistics     # Stats joueur
```

###  Standings (2 endpoints)
```
GET  /standings                   # Classement
GET  /standings/{season_id}/full  # Classement complet
```

### Events (5 endpoints)

```
GET  /events                       # Tous les événements (filtres: fixture, team, player, type)
GET  /events/{event_id}            # Détail d'un événement
GET  /events/goals/all             # Tous les buts (filtres: fixture, player, team)
GET  /events/cards/all             # Tous les cartons (filtres: fixture, player, card_type)
GET  /events/top-scorers           # Classement des buteurs (filtres: league, season, team)
```
### Statistics (4 endpoints)

```
GET  /statistics/match/{fixture_id}                     # Stats détaillées d'un match avec comparaisons
GET  /statistics/player/{player_id}/season/{season_id}  # Stats d'un joueur pour une saison
GET  /statistics/team/{team_id}/season/{season_id}      # Stats d'une équipe pour une saison
GET  /statistics/league/{league_id}/top-teams           # Meilleures équipes d'une league
```
### Lineups (5 endpoints)

```
GET  /lineups                                           # Toutes les compositions (filtres: fixture, team, player, starter)
GET  /lineups/player/{player_id}/history                # Historique des compositions d'un joueur
GET  /lineups/team/{team_id}/most-used-formation        # Formation la plus utilisée par une équipe
GET  /lineups/fixture/{fixture_id}/captains             # Capitaines d'un match
```

### Managers (6 endpoints)

```
GET  /managers                                          # Tous les entraîneurs (filtres: nationality, current_only, search)
GET  /managers/{manager_id}                             # Détail d'un entraîneur
GET  /managers/{manager_id}/teams                       # Historique des équipes d'un entraîneur
GET  /managers/{manager_id}/statistics                  # Statistiques d'un entraîneur
GET  /managers/team/{team_id}/history                   # Historique des entraîneurs d'une équipe
```

### Seasons  (5 endpoints)

```
GET  /seasons                                           # Toutes les saisons (filtres: league, current, year)
GET  /seasons/{season_id}                               # Détail d'une saison
GET  /seasons/{season_id}/fixtures                      # Tous les matchs d'une saison
GET  /seasons/{season_id}/standings                     # Classement d'une saison
GET  /seasons/{season_id}/statistics                    # Statistiques globales d'une saison
```

###  Utilitaires (2 endpoints)
```
GET  /                            # Root
GET  /health                      # Health check
```

**TOTAL : 44 ENDPOINTS** 

---

##  FONCTIONNALITÉS IMPLÉMENTÉES

### Filtres Avancés
- **Fixtures**  :  league, season, team, date, status, round, live
- **Teams**     :  country, national, search
- **Players**   :  team, position, search
- **Standings** :  league, season, group
- **Events**    :  fixture, team, player, type
- **Lineups**   :  fixture, team, player, starter
- **Managers**  :  nationality, current_only, search
- **Seasons**   :  league, current, year

### Format de Réponse Standard
```json
{
  "success": true,
  "data": {...},
  "errors": [...],
  "meta": {...}
}
```

### Documentation Auto-Générée
- **Swagger UI** : `/docs`
- **ReDoc** : `/redoc`
- Documentation interactive complète

###  CORS Configuré
- Prêt pour le frontend
- Configurable par environnement

###  Middleware Performance
- Header `X-Process-Time` sur chaque requête

### Gestion d'Erreurs
- HTTPException pour erreurs connues
- Handler global pour erreurs inattendues
- Messages d'erreur clairs

---

##  LANCEMENT RAPIDE


### 1. Installer les dépendances
```bash
cd gogainde-data
make install
```

### 2. Initialiser la DB
```bash
make db-init
```

### 3. (Optionnel) Scraper les données
```bash
make scrape-afcon
```

### 4. Lancer l'API
```bash
make dev
```

###56. Accéder à l'API
- **API** : http://localhost:8000
- **Swagger** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

---

##  EXEMPLES D'UTILISATION

### Récupérer les matchs du jour
```bash
curl "http://localhost:8000/fixtures?date=2024-01-15"
```

### Récupérer les joueurs du Sénégal
```bash
curl "http://localhost:8000/teams/1/players"
```

### Récupérer les statistiques d'un match
```bash
curl "http://localhost:8000/fixtures/1/statistics"
```

### Récupérer le classement du groupe A
```bash
curl "http://localhost:8000/standings?league_id=1&group=A"
```

### Récupérer les matchs en cours
```bash
curl "http://localhost:8000/fixtures/live/all"
```

### Récupérer des événements
```bash
### Tous les buts d'un match
curl "http://localhost:8000/events/goals/all?fixture_id=1"

# Cartons d'un joueur
curl "http://localhost:8000/events/cards/all?player_id=5"

# Top buteurs d'une saison
curl "http://localhost:8000/events/top-scorers?season_id=1&limit=10"
```

### Récupérer des Statistics
```bash
# Stats détaillées d'un match avec comparaisons
curl "http://localhost:8000/statistics/match/1"

# Stats d'un joueur pour une saison
curl "http://localhost:8000/statistics/player/5/season/1"

# Stats d'une équipe pour une saison
curl "http://localhost:8000/statistics/team/1/season/1"

# Meilleures équipes d'une league
curl "http://localhost:8000/statistics/league/1/top-teams?limit=5"
```

### Récupérer les compositions
```bash
# Compositions d'un match
curl "http://localhost:8000/lineups?fixture_id=1"

# Historique des compositions d'un joueur
curl "http://localhost:8000/lineups/player/5/history?season_id=1"

# Formation la plus utilisée
curl "http://localhost:8000/lineups/team/1/most-used-formation"

# Capitaines d'un match
curl "http://localhost:8000/lineups/fixture/1/captains"
```

### Réxupérer les Managers
```bash
# Tous les entraîneurs
curl "http://localhost:8000/managers"

# Entraîneurs actifs
curl "http://localhost:8000/managers?current_only=true"

# Historique des équipes d'un entraîneur
curl "http://localhost:8000/managers/1/teams"

# Historique des entraîneurs d'une équipe
curl "http://localhost:8000/managers/team/1/history"
```

### Récuperer les saisons

```bash
# Toutes les saisons
curl "http://localhost:8000/seasons"

# Saisons en cours
curl "http://localhost:8000/seasons?current=true"

# Matchs d'une saison
curl "http://localhost:8000/seasons/1/fixtures"

# Stats d'une saison
curl "http://localhost:8000/seasons/1/statistics"
```
---

##  TESTER L'API

### Avec les tests automatisés
```bash
make test
```

### Manuellement
```bash
# Via navigateur
http://localhost:8000/docs

# Via curl
curl http://localhost:8000/leagues
```

---

## STRUCTURE DES DONNÉES

### Request
```
Query Parameters → Pydantic Models → Validation
```

### Response
```
Database → SQLAlchemy Models → Pydantic Schemas → JSON
``` 
`

### Documentation
```python
# Accéder à la doc interactive
http://localhost:8000/docs
```

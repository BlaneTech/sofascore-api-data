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
├── leagues.py          3 endpoints
├── teams.py            4 endpoints
├── fixtures.py         7 endpoints
├── players.py          3 endpoints
└── standings.py        2 endpoints

Total: 19 endpoints
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

###  Utilitaires (2 endpoints)
```
GET  /                            # Root
GET  /health                      # Health check
```

**TOTAL : 21 ENDPOINTS** 

---

##  FONCTIONNALITÉS IMPLÉMENTÉES

### Filtres Avancés
- **Fixtures** : league, season, team, date, status, round, live
- **Teams** : country, national, search
- **Players** : team, position, search
- **Standings** : league, season, group

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

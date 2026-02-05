# 📊 Documentation des Modèles de Données.

## 🗂️ Modèles

### 1. League (Compétition)

Représente une compétition (CAN, qualifications, etc.)

```python
class League:
    id: int (PK)
    sofascore_id: int (UNIQUE)
    name: str
    slug: str
    type: TournamentType (ENUM)
    country: str
    logo_url: str
```

**Relations:**
- `seasons` → One-to-Many avec Season
- `fixtures` → One-to-Many avec Fixture

---

### 2. Season (Saison)

Représente une édition d'une compétition

```python
class Season:
    id: int (PK)
    sofascore_id: int (UNIQUE)
    league_id: int (FK → League)
    year: str
    name: str
    start_date: Date
    end_date: Date
    current: bool
```

**Relations:**
- `league` → Many-to-One avec League
- `fixtures` → One-to-Many avec Fixture
- `standings` → One-to-Many avec Standing

---

### 3. Team (Équipe)

Représente une équipe nationale

```python
class Team:
    id: int (PK)
    sofascore_id: int (UNIQUE)
    name: str
    slug: str
    short_name: str
    code: str
    country: str
    national: bool
    logo_url: str
    founded: int
    primary_color: str
    secondary_color: str
```

**Relations:**
- `home_fixtures` → One-to-Many avec Fixture (domicile)
- `away_fixtures` → One-to-Many avec Fixture (extérieur)
- `players` → One-to-Many avec Player
- `team_managers` → One-to-Many avec TeamManager
- `match_statistics` → One-to-Many avec MatchStatistics
- `team_statistics` → One-to-Many avec TeamStatistics

---

### 4. Manager (Entraîneur) ✨ NOUVEAU

Représente un entraîneur

```python
class Manager:
    id: int (PK)
    sofascore_id: int (UNIQUE)
    name: str
    slug: str
    first_name: str
    last_name: str
    date_of_birth: Date
    nationality: str
    photo_url: str
```

**Relations:**
- `team_managers` → One-to-Many avec TeamManager

---

### 5. TeamManager (Historique Entraîneur) ✨ NOUVEAU

Représente l'historique des entraîneurs par équipe

```python
class TeamManager:
    id: int (PK)
    team_id: int (FK → Team)
    manager_id: int (FK → Manager)
    start_date: Date
    end_date: Date (nullable)
    is_current: bool
```

**Contraintes:**
- UNIQUE (team_id, manager_id, start_date)

**Relations:**
- `team` → Many-to-One avec Team
- `manager` → Many-to-One avec Manager

---

### 6. Player (Joueur)

Représente un joueur

```python
class Player:
    id: int (PK)
    sofascore_id: int (UNIQUE)
    team_id: int (FK → Team, nullable)
    name: str
    slug: str
    short_name: str
    first_name: str
    last_name: str
    position: str
    jersey_number: int
    date_of_birth: Date
    height: int
    preferred_foot: str
    photo_url: str
```

**Relations:**
- `team` → Many-to-One avec Team
- `statistics` → One-to-Many avec PlayerStatistics
- `events` → One-to-Many avec MatchEvent
- `assists` → One-to-Many avec MatchEvent

---

### 7. Fixture (Match)

Représente un match

```python
class Fixture:
    id: int (PK)
    sofascore_id: int (UNIQUE)
    league_id: int (FK → League)
    season_id: int (FK → Season)
    home_team_id: int (FK → Team)
    away_team_id: int (FK → Team)
    date: DateTime
    timestamp: int
    round: int
    round_name: str
    group_name: str
    group_sign: str
    status: MatchStatus (ENUM)
    status_long: str
    elapsed: int
    home_score: int
    away_score: int
    home_score_period1: int
    away_score_period1: int
    home_score_period2: int
    away_score_period2: int
    home_score_normaltime: int
    away_score_normaltime: int
    is_live: bool
    has_lineups: bool
    has_statistics: bool
    has_events: bool
```

**Relations:**
- `league` → Many-to-One avec League
- `season` → Many-to-One avec Season
- `home_team` → Many-to-One avec Team
- `away_team` → Many-to-One avec Team
- `events` → One-to-Many avec MatchEvent
- `lineups` → One-to-Many avec Lineup
- `match_statistics` → One-to-Many avec MatchStatistics

---

### 8. MatchEvent (Événement de Match)

Représente un événement dans un match (but, carton, etc.)

```python
class MatchEvent:
    id: int (PK)
    fixture_id: int (FK → Fixture)
    team_id: int (FK → Team)
    player_id: int (FK → Player, nullable)
    assist_player_id: int (FK → Player, nullable)
    type: EventType (ENUM)
    minute: int
    extra_minute: int
    detail: str
    comments: Text
```

**Relations:**
- `fixture` → Many-to-One avec Fixture
- `player` → Many-to-One avec Player
- `assist_player` → Many-to-One avec Player
- `team` → Many-to-One avec Team

---

### 9. Lineup (Composition)

Représente la composition d'une équipe pour un match

```python
class Lineup:
    id: int (PK)
    fixture_id: int (FK → Fixture)
    team_id: int (FK → Team)
    player_id: int (FK → Player)
    formation: str
    position: str
    starter: bool
    rating: float
    minutes_played: int
    captain: bool
    substitute: bool
```

**Contraintes:**
- UNIQUE (fixture_id, team_id, player_id) ✨

**Relations:**
- `fixture` → Many-to-One avec Fixture
- `team` → Many-to-One avec Team
- `player` → Many-to-One avec Player

---

### 10. MatchStatistics (Statistiques de Match) ✨

Représente les statistiques d'une équipe pour un match

```python
class MatchStatistics:
    id: int (PK)
    fixture_id: int (FK → Fixture)
    team_id: int (FK → Team)
    shots_on_goal: int
    shots_off_goal: int
    total_shots: int
    blocked_shots: int
    shots_inside_box: int
    shots_outside_box: int
    fouls: int
    corners: int
    offsides: int
    ball_possession: float
    passes: int
    pass_accuracy: float
    tackles: int
    saves: int
    yellow_cards: int
    red_cards: int
    # ... (40+ champs de statistiques)
```

**Contraintes:**
- UNIQUE (fixture_id, team_id) ✨
  → Garantit 2 enregistrements par match (home + away)

**Relations:**
- `fixture` → Many-to-One avec Fixture
- `team` → Many-to-One avec Team

---

### 11. PlayerStatistics

Représente les statistiques d'un joueur pour un match

```python
class PlayerStatistics:
    id: int (PK)
    player_id: int (FK → Player)
    fixture_id: int (FK → Fixture)
    rating: float
    minutes_played: int
    goals: int
    assists: int
    shots: int
    shots_on_target: int
    passes: int
    pass_accuracy: float
    tackles: int
    interceptions: int
    fouls: int
    yellow_cards: int
    red_cards: int
    dribbles: int
    dribble_attempts: int
```

**Relations:**
- `player` → Many-to-One avec Player
- `fixture` → Many-to-One avec Fixture

---

### 12. TeamStatistics

Représente les statistiques globales d'une équipe

```python
class TeamStatistics:
    id: int (PK)
    team_id: int (FK → Team)
    total_matches: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
```

**Relations:**
- `team` → Many-to-One avec Team

---

### 13. Standing (Classement)

Représente le classement d'une équipe dans une compétition

```python
class Standing:
    id: int (PK)
    sofascore_id: int (UNIQUE)
    season_id: int (FK → Season)
    team_id: int (FK → Team)
    group: str
    rank: int
    total_matches: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
```

**Contraintes:**
- UNIQUE (season_id, team_id, group) ✨

**Relations:**
- `season` → Many-to-One avec Season
- `team` → Many-to-One avec Team

---

## 🔐 Index

Les index suivants sont créés pour optimiser les performances :

- `sofascore_id` sur toutes les tables principales
- `league_id`, `season_id` sur Season
- `league_id`, `season_id`, `home_team_id`, `away_team_id`, `date`, `status` sur Fixture
- `fixture_id`, `team_id`, `player_id` sur MatchEvent, Lineup
- `fixture_id`, `team_id` sur MatchStatistics
- `player_id`, `fixture_id` sur PlayerStatistics
- `team_id` sur TeamStatistics, Player
- `season_id`, `team_id` sur Standing

---

## 🎯 Règles d'Intégrité

1. **Un match a exactement 2 équipes** (home et away)
2. **Un match a exactement 2 enregistrements de statistiques** (contrainte unique)
3. **Un joueur ne peut pas être dans 2 compositions différentes pour le même match** (contrainte unique)
4. **Un entraîneur ne peut pas avoir 2 périodes identiques avec la même équipe** (contrainte unique)

---

## 📋 Enums

### TournamentType
```python
WORLD_CUP = "world_cup"
AFCON = "afcon"
AFCON_QUALIFIERS = "afcon_qualifiers"
WC_QUALIFIERS = "wc_qualifiers"
FRIENDLY = "friendly"
OTHER = "other"
```

### MatchStatus
```python
NOT_STARTED = "notstarted"
IN_PROGRESS = "inprogress"
FINISHED = "finished"
POSTPONED = "postponed"
CANCELLED = "cancelled"
ABANDONED = "abandoned"
```

### EventType
```python
GOAL = "goal"
YELLOW_CARD = "yellowCard"
RED_CARD = "redCard"
SUBSTITUTION = "substitution"
VAR = "var"
PENALTY_MISSED = "penaltyMissed"
```

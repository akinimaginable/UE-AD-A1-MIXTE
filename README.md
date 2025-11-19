# UE-AD-A1-MIXTE - Microservices avec API Mixtes

## Architecture

Ce projet implémente une architecture de microservices avec des API mixtes (GraphQL, gRPC, REST) et utilise MongoDB comme base de données.

### Services

1. **Movie Service** (GraphQL) - Port 3001
   - Gestion des films
   - API GraphQL avec queries et mutations
   - Base de données: MongoDB (collection `movies`)

2. **Booking Service** (GraphQL) - Port 3201
   - Gestion des réservations
   - API GraphQL avec queries et mutations
   - Appels inter-services: Movie (GraphQL), Schedule (gRPC), User (REST)
   - Base de données: MongoDB (collection `bookings`)

3. **Schedule Service** (gRPC) - Port 3002
   - Gestion du planning des films
   - API gRPC avec méthodes GetAll, GetByDate, AddToSchedule, RemoveFromSchedule
   - Base de données: MongoDB (collection `schedule`)

4. **User Service** (REST) - Port 3203
   - Gestion des utilisateurs
   - API REST avec endpoints CRUD
   - Base de données: MongoDB (collection `users`)

5. **MongoDB** - Port 27017
   - Base de données principale pour tous les services

6. **Mongo Express** - Port 8081
   - Interface web pour visualiser et gérer MongoDB

### Diagramme d'Architecture

```
┌─────────────┐
│   Client    │
│  (Insomnia) │
└──────┬──────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌─────────────┐                      ┌─────────────┐
│   Booking   │                      │    User     │
│  (GraphQL)  │                      │   (REST)    │
│  Port 3201  │                      │  Port 3203  │
└──────┬──────┘                      └────────────┘
       │                                     ▲
       │                                     │
       ├──────────────┬──────────────────────┘
       │              │
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│    Movie    │  │   Schedule  │
│  (GraphQL)  │  │   (gRPC)    │
│  Port 3001  │  │  Port 3002  │
└─────────────┘  └─────────────┘
       │              │
       └──────┬───────┘
              │
              ▼
       ┌─────────────┐
       │   MongoDB   │
       │  Port 27017 │
       └─────────────┘
```

### Interactions entre Services

- **Booking → Movie**: Requêtes GraphQL (POST http://movie:3001/graphql)
- **Booking → Schedule**: Appels gRPC (schedule:3002)
- **Booking → User**: Requêtes REST (GET http://user:3203/users/{id})
- **Movie → User**: Requêtes REST pour vérifier les droits admin

## Organisation du Projet

```
UE-AD-A1-MIXTE/
├── booking/              # Service de réservation (GraphQL)
│   ├── booking.py         # Point d'entrée Flask + GraphQL
│   ├── booking.graphql    # Schéma GraphQL
│   ├── resolvers.py       # Résolveurs GraphQL + MongoDB
│   ├── data/
│   │   └── bookings.json  # Données initiales
│   └── Dockerfile
├── movie/                 # Service de films (GraphQL)
│   ├── movie.py           # Point d'entrée Flask + GraphQL
│   ├── movie.graphql      # Schéma GraphQL
│   ├── resolvers.py       # Résolveurs GraphQL + MongoDB
│   ├── data/
│   │   └── movies.json    # Données initiales
│   └── Dockerfile
├── schedule/              # Service de planning (gRPC)
│   ├── schedule.py        # Serveur gRPC + MongoDB
│   ├── schedule.proto     # Définition protobuf
│   ├── schedule_pb2.py    # Code généré (protobuf)
│   ├── schedule_pb2_grpc.py # Code généré (gRPC)
│   ├── data/
│   │   └── times.json     # Données initiales
│   └── Dockerfile
├── user/                  # Service d'utilisateurs (REST)
│   ├── user.py            # API REST Flask + MongoDB
│   ├── data/
│   │   └── users.json     # Données initiales
│   └── Dockerfile
├── docker-compose.yml     # Configuration Docker Compose
├── requirements.txt       # Dépendances Python
└── README.md              # Ce fichier
```

## Déploiement

### Prérequis

- Docker Desktop installé et démarré
- Docker Compose (inclus avec Docker Desktop)

### Démarrage

1. **Cloner le dépôt** (si nécessaire)

2. **Démarrer tous les services**:
```bash
docker-compose up --build
```

Cette commande va:
- Construire les images Docker pour tous les services
- Démarrer MongoDB
- Démarrer Mongo Express
- Démarrer tous les microservices
- Initialiser automatiquement les données depuis les fichiers JSON si les collections sont vides

### Accès aux Services

- **Movie (GraphQL)**: http://localhost:3001/graphql
- **Booking (GraphQL)**: http://localhost:3201/graphql
- **Schedule (gRPC)**: localhost:3002 (nécessite un client gRPC)
- **User (REST)**: http://localhost:3203/users
- **Mongo Express**: http://localhost:8081

### Arrêt

```bash
docker-compose down
```

Pour supprimer aussi les volumes (données MongoDB):
```bash
docker-compose down -v
```

## Utilisation

### Exemples de Requêtes

#### Movie Service (GraphQL)

**Query - Récupérer tous les films**:
```graphql
query {
  all_movies {
    id
    title
    rating
    director
  }
}
```

**Query - Récupérer un film par ID**:
```graphql
query {
  movie_by_id(id: "267eedb8-0f5d-42d5-8f43-72426b9fb3e6") {
    id
    title
    rating
    director
  }
}
```

**Mutation - Ajouter un film** (admin requis):
```graphql
mutation {
  add_movie(movie: {
    id: "new-movie-id"
    title: "Nouveau Film"
    rating: 8.5
    director: "Réalisateur"
    author: "chris_rivers"
  }) {
    message
    movie {
      id
      title
    }
  }
}
```

#### Booking Service (GraphQL)

**Query - Réservations détaillées d'un utilisateur**:
```graphql
query {
  detailed_bookings_by_user(userid: "chris_rivers") {
    userid
    bookings {
      date
      movies {
        movie {
          id
          title
          rating
        }
        schedule {
          date
          movies
        }
      }
    }
  }
}
```

**Mutation - Créer une réservation**:
```graphql
mutation {
  create_booking(input: {
    userid: "chris_rivers"
    movieid: "267eedb8-0f5d-42d5-8f43-72426b9fb3e6"
    date: "20151201"
  }) {
    message
    booking {
      userid
      movieid
      date
    }
  }
}
```

#### User Service (REST)

**GET - Récupérer tous les utilisateurs**:
```bash
GET http://localhost:3203/users
```

**GET - Récupérer un utilisateur par ID**:
```bash
GET http://localhost:3203/users/chris_rivers
```

**GET - Récupérer les administrateurs**:
```bash
GET http://localhost:3203/users/admin
```

**POST - Créer un utilisateur**:
```bash
POST http://localhost:3203/users
Content-Type: application/json

{
  "id": "new_user",
  "name": "Nouvel Utilisateur",
  "last_active": 1360031000,
  "role": "user"
}
```

## Scénarios Insomnia préremplis

- Le fichier `UE-AD-A1-MIXTE-Insomnia.json` contient **toutes les routes** prêtes à l'emploi (User REST, Movie/Booking GraphQL).
- Deux dossiers dédiés **DÉMO ORAL** sont inclus :
  - `🎬 Scénario Utilisateur` : création de réservation puis consultation détaillée (appels Movie + Schedule + MongoDB).
  - `👑 Scénario Administrateur` : consultation globale, ajout de film, puis tentative d'ajout par un non-admin (erreur attendue pour démontrer la sécurité).
- Chaque requête est **préremplie avec des données valides** (IDs MongoDB existants, dates réellement programmées).
- Import direct :
  1. Ouvrir Insomnia → `Create` → `Import From` → `File`.
  2. Sélectionner `UE-AD-A1-MIXTE-Insomnia.json`.
  3. Les requêtes peuvent être envoyées immédiatement après `docker-compose up`.

## Base de Données MongoDB

### Collections

- `movies`: Films disponibles
- `bookings`: Réservations des utilisateurs
- `schedule`: Planning des films par date
- `users`: Utilisateurs du système

### Initialisation

Les données sont automatiquement initialisées depuis les fichiers JSON lors du premier démarrage si les collections sont vides.

### Accès via Mongo Express

1. Ouvrir http://localhost:8081
2. Se connecter avec:
   - Username: `root`
   - Password: `*65%8XPuGaQ#`

## Utilisateurs Administrateurs

Par défaut, les utilisateurs suivants ont le rôle `admin`:
- `chris_rivers`
- `michael_scott`

Les autres utilisateurs ont le rôle `user`.

## Technologies Utilisées

- **Python 3.14**
- **Flask**: Framework web pour REST et GraphQL
- **Ariadne**: Bibliothèque GraphQL pour Python
- **gRPC**: Communication inter-services
- **MongoDB**: Base de données NoSQL
- **pymongo**: Driver Python pour MongoDB
- **Docker & Docker Compose**: Containerisation

## Notes Techniques

### Communication Inter-Services

Les services communiquent via les noms de services Docker:
- `movie:3001` pour le service Movie
- `schedule:3002` pour le service Schedule
- `user:3203` pour le service User

### Gestion des Erreurs

- Les erreurs GraphQL sont retournées dans le format standard GraphQL
- Les erreurs gRPC utilisent les codes de statut gRPC
- Les erreurs REST utilisent les codes HTTP standards

### Sécurité

- Les opérations d'administration (ajout/suppression de films) nécessitent un utilisateur avec le rôle `admin`
- Les réservations vérifient l'existence des films et leur programmation avant création

## Développement

### Structure des Résolveurs

Chaque service GraphQL contient:
- Des **queries**: Opérations de lecture
- Des **mutations**: Opérations d'écriture

### Tests

Utiliser Insomnia ou Postman pour tester les API:
- Collection Postman disponible: `UE-AD-A1-MIXTE.postman_collection.json`

### Logs

Les logs de chaque service sont visibles dans la console Docker Compose.

## Auteur

Projet réalisé dans le cadre de l'UE AD (Architecture Distribuée) - IMT Atlantique

import json
import os
import requests
from pymongo import MongoClient
from bson.json_util import dumps
from urllib.parse import quote_plus

is_admin_cache = {}
PERSISTENCE_TYPE = os.getenv("PERSISTENCE_TYPE", "MONGODB")
JSON_FILE_PATH = "{}/data/movies.json".format(".")

# Connexion MongoDB
# Le mot de passe est encodé dans docker-compose.yml, sinon on utilise l'encodage par défaut
default_password = quote_plus("*65%8XPuGaQ#")
MONGO_URL = os.getenv(
    "MONGO_URL", f"mongodb://root:{default_password}@localhost:27017/"
)

client = None
db = None
collection = None

if PERSISTENCE_TYPE == "MONGODB":
    # Connexion avec retry automatique (pymongo gère les reconnexions)
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client["movies"]
    collection = db["movies"]

    # Initialisation des données depuis JSON si la collection est vide
    if collection.count_documents({}) == 0:
        print("Initialisation de la base de données MongoDB avec les données JSON...")
        with open(JSON_FILE_PATH, "r") as jsf:
            movies_data = json.load(jsf)["movies"]
            if movies_data:
                collection.insert_many(movies_data)
                print(f"Films chargés: {len(movies_data)} films")
    else:
        print(
            f"Base de données MongoDB déjà initialisée: {collection.count_documents({})} films"
        )
else:
    print(f"Utilisation de la persistance JSON (Fichier: {JSON_FILE_PATH})")


def get_json_data():
    try:
        with open(JSON_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"movies": []}


def save_json_data(data):
    with open(JSON_FILE_PATH, "w") as f:
        json.dump(data, f, indent=4)


def check_admin(author) -> bool:
    """Vérifie si l'utilisateur est un administrateur"""
    if not author:
        return False

    if author in is_admin_cache:
        return is_admin_cache[author]

    try:
        # Utiliser le nom du service Docker
        resp = requests.get(f"http://user:3203/users/{author}")
        if resp.status_code == 200:
            data = resp.json()
            is_admin = data.get("role", "") == "admin"
            is_admin_cache[author] = is_admin
            return is_admin
        else:
            return False
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False


# ============================================================================
# QUERY RESOLVERS
# ============================================================================


def all_movies_resolver(obj, info):
    """Récupère tous les films"""
    if PERSISTENCE_TYPE == "MONGODB":
        movies_list = list(collection.find({}))
        # Convertir ObjectId en string pour JSON
        for movie in movies_list:
            if "_id" in movie:
                movie["_id"] = str(movie["_id"])
        return movies_list
    else:
        data = get_json_data()
        return data.get("movies", [])


def movie_by_id_resolver(obj, info, id):
    """Récupère un film par son ID"""
    if PERSISTENCE_TYPE == "MONGODB":
        movie = collection.find_one({"id": str(id)})
        if movie and "_id" in movie:
            movie["_id"] = str(movie["_id"])
        return movie
    else:
        data = get_json_data()
        for movie in data.get("movies", []):
            if movie["id"] == str(id):
                return movie
        return None


def movie_by_title_resolver(obj, info, title):
    """Récupère un film par son titre"""
    if PERSISTENCE_TYPE == "MONGODB":
        movie = collection.find_one(
            {"title": {"$regex": f"^{title}$", "$options": "i"}}
        )
        if movie and "_id" in movie:
            movie["_id"] = str(movie["_id"])
        return movie
    else:
        data = get_json_data()
        import re

        pattern = re.compile(f"^{title}$", re.IGNORECASE)
        for movie in data.get("movies", []):
            if pattern.match(movie["title"]):
                return movie
        return None


# ============================================================================
# MUTATION RESOLVERS
# ============================================================================


def add_movie_resolver(obj, info, movie):
    """Ajoute un nouveau film"""
    author = movie.get("author")

    if not check_admin(author):
        raise Exception("Accès refusé, administrateur requis")

    new_movie = {
        "id": movie["id"],
        "title": movie["title"],
        "rating": movie["rating"],
        "director": movie["director"],
    }

    if PERSISTENCE_TYPE == "MONGODB":
        # Vérification de l'unicité de l'ID
        existing_movie = collection.find_one({"id": str(movie["id"])})
        if existing_movie:
            raise Exception("Film ID déjà existant")

        collection.insert_one(new_movie)
        if "_id" in new_movie:
            new_movie["_id"] = str(new_movie["_id"])
    else:
        data = get_json_data()
        movies = data.get("movies", [])
        for m in movies:
            if m["id"] == str(movie["id"]):
                raise Exception("Film ID déjà existant")

        movies.append(new_movie)
        data["movies"] = movies
        save_json_data(data)

    return {"message": "Film ajouté avec succès", "movie": new_movie}


def update_movie_rating_resolver(obj, info, id, rating, author):
    """Met à jour la note d'un film"""
    if not check_admin(author):
        raise Exception("Accès refusé, administrateur requis")

    if PERSISTENCE_TYPE == "MONGODB":
        result = collection.update_one(
            {"id": str(id)}, {"$set": {"rating": float(rating)}}
        )

        if result.matched_count == 0:
            raise Exception("Film ID non trouvé")

        movie = collection.find_one({"id": str(id)})
        if movie and "_id" in movie:
            movie["_id"] = str(movie["_id"])
        return {"message": "Note mise à jour avec succès", "movie": movie}
    else:
        data = get_json_data()
        movies = data.get("movies", [])
        found = False
        updated_movie = None
        for m in movies:
            if m["id"] == str(id):
                m["rating"] = float(rating)
                updated_movie = m
                found = True
                break

        if not found:
            raise Exception("Film ID non trouvé")

        data["movies"] = movies
        save_json_data(data)

        return {"message": "Note mise à jour avec succès", "movie": updated_movie}


def delete_movie_resolver(obj, info, id, author):
    """Supprime un film"""
    if not check_admin(author):
        raise Exception("Accès refusé, administrateur requis")

    if PERSISTENCE_TYPE == "MONGODB":
        movie = collection.find_one({"id": str(id)})
        if not movie:
            raise Exception("Film ID non trouvé")

        collection.delete_one({"id": str(id)})
        if "_id" in movie:
            movie["_id"] = str(movie["_id"])

        return {"message": "Film supprimé avec succès", "movie": movie}
    else:
        data = get_json_data()
        movies = data.get("movies", [])
        found = False
        deleted_movie = None
        new_movies = []

        for m in movies:
            if m["id"] == str(id):
                deleted_movie = m
                found = True
            else:
                new_movies.append(m)

        if not found:
            raise Exception("Film ID non trouvé")

        data["movies"] = new_movies
        save_json_data(data)

        return {"message": "Film supprimé avec succès", "movie": deleted_movie}


# ============================================================================
# RESOLVER MAP
# ============================================================================


def resolve_queries():
    """Associe les résolveurs de requêtes"""
    return {
        "all_movies": all_movies_resolver,
        "movie_by_id": movie_by_id_resolver,
        "movie_by_title": movie_by_title_resolver,
    }


def resolve_mutations():
    """Associe les résolveurs de mutations"""
    return {
        "add_movie": add_movie_resolver,
        "update_movie_rating": update_movie_rating_resolver,
        "delete_movie": delete_movie_resolver,
    }

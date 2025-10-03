import json
import requests

is_admin_cache = {}

# Chargement de la base de données des films
with open('{}/data/movies.json'.format("."), 'r') as jsf:
    movies = json.load(jsf)["movies"]
    print("Films chargés:", len(movies), "films")


def write_movies_to_file(movies_data):
    """Sauvegarde les données de films dans le fichier JSON"""
    with open('{}/data/movies.json'.format("."), 'w') as f:
        full = {'movies': movies_data}
        json.dump(full, f, indent=4)


def check_admin(author) -> bool:
    """Vérifie si l'utilisateur est un administrateur"""
    if not author:
        return False
    
    if author in is_admin_cache:
        return is_admin_cache[author]

    try:
        resp = requests.get(f"http://localhost:3203/users/{author}")
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
    return movies


def movie_by_id_resolver(obj, info, id):
    """Récupère un film par son ID"""
    for movie in movies:
        if str(movie["id"]) == str(id):
            return movie
    return None


def movie_by_title_resolver(obj, info, title):
    """Récupère un film par son titre"""
    for movie in movies:
        if str(movie["title"]).lower() == str(title).lower():
            return movie
    return None


# ============================================================================
# MUTATION RESOLVERS
# ============================================================================

def add_movie_resolver(obj, info, movie):
    """Ajoute un nouveau film"""
    author = movie.get('author')
    
    if not check_admin(author):
        raise Exception("Accès refusé, administrateur requis")
    
    # Vérification de l'unicité de l'ID
    for existing_movie in movies:
        if str(existing_movie["id"]) == str(movie["id"]):
            raise Exception("Film ID déjà existant")
    
    # Création du nouveau film sans le champ author
    new_movie = {
        "id": movie["id"],
        "title": movie["title"],
        "rating": movie["rating"],
        "director": movie["director"]
    }
    
    movies.append(new_movie)
    write_movies_to_file(movies)
    
    return {
        "message": "Film ajouté avec succès",
        "movie": new_movie
    }


def update_movie_rating_resolver(obj, info, id, rating, author):
    """Met à jour la note d'un film"""
    if not check_admin(author):
        raise Exception("Accès refusé, administrateur requis")
    
    for movie in movies:
        if str(movie["id"]) == str(id):
            movie["rating"] = float(rating)
            write_movies_to_file(movies)
            return {
                "message": "Note mise à jour avec succès",
                "movie": movie
            }
    
    raise Exception("Film ID non trouvé")


def delete_movie_resolver(obj, info, id, author):
    """Supprime un film"""
    if not check_admin(author):
        raise Exception("Accès refusé, administrateur requis")
    
    for movie in movies:
        if str(movie["id"]) == str(id):
            movies.remove(movie)
            write_movies_to_file(movies)
            return {
                "message": "Film supprimé avec succès",
                "movie": movie
            }
    
    raise Exception("Film ID non trouvé")


# ============================================================================
# RESOLVER MAP
# ============================================================================

def resolve_queries():
    """Associe les résolveurs de requêtes"""
    return {
        "all_movies": all_movies_resolver,
        "movie_by_id": movie_by_id_resolver,
        "movie_by_title": movie_by_title_resolver
    }


def resolve_mutations():
    """Associe les résolveurs de mutations"""
    return {
        "add_movie": add_movie_resolver,
        "update_movie_rating": update_movie_rating_resolver,
        "delete_movie": delete_movie_resolver
    }


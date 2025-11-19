import json
import os
import requests
import grpc
import schedule_pb2
import schedule_pb2_grpc
from pymongo import MongoClient
from urllib.parse import quote_plus

# URLs des autres microservices (utiliser les noms de services Docker)
MOVIE_SERVICE_URL = "http://movie:3001"  # Service Movie en GraphQL
SCHEDULE_SERVICE_URL = "schedule:3002"  # Service Schedule en gRPC
USER_SERVICE_URL = "http://user:3203"

# Connexion MongoDB
# Le mot de passe est encodé dans docker-compose.yml, sinon on utilise l'encodage par défaut
default_password = quote_plus("*65%8XPuGaQ#")
MONGO_URL = os.getenv("MONGO_URL", f"mongodb://root:{default_password}@localhost:27017/")
# Connexion avec retry automatique (pymongo gère les reconnexions)
client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client["bookings"]
collection = db["bookings"]

# Initialisation des données depuis JSON si la collection est vide
if collection.count_documents({}) == 0:
    print("Initialisation de la base de données MongoDB avec les données JSON...")
    with open('{}/data/bookings.json'.format("."), "r") as jsf:
        bookings_data = json.load(jsf)["bookings"]
        if bookings_data:
            collection.insert_many(bookings_data)
            print(f"Réservations chargées: {len(bookings_data)} utilisateurs")
else:
    print(f"Base de données MongoDB déjà initialisée: {collection.count_documents({})} réservations")


def get_movie_details(movie_id):
    """Récupère les détails d'un film depuis le service Movie via GraphQL"""
    try:
        # Requête GraphQL vers le service Movie
        query = """
        query {
            movie_by_id(id: "%s") {
                id
                title
                rating
                director
            }
        }
        """ % movie_id
        
        response = requests.post(f"{MOVIE_SERVICE_URL}/graphql", json={'query': query})
        if response.status_code == 200:
            result = response.json()
            # GraphQL retourne les données dans result['data']
            if 'data' in result and result['data']['movie_by_id']:
                return result['data']['movie_by_id']
        return None
    except requests.RequestException:
        return None


def get_schedule_by_date(date):
    """Récupère le planning d'une date depuis le service Schedule via gRPC"""
    try:
        # Connexion au service Schedule via gRPC
        with grpc.insecure_channel(SCHEDULE_SERVICE_URL) as channel:
            stub = schedule_pb2_grpc.ScheduleStub(channel)
            request = schedule_pb2.Date(date=date)
            response = stub.GetByDate(request)
            
            # Le proto retourne maintenant une liste, on prend le premier élément s'il existe
            if response.list and len(response.list) > 0:
                day_schedule = response.list[0]
                return {
                    "date": day_schedule.date,
                    "movies": list(day_schedule.movies)
                }
            return None
    except grpc.RpcError as e:
        print(f"Erreur gRPC lors de la récupération du planning: {e}")
        return None


def get_schedule_details(movie_id, date):
    """Vérifie si un film est programmé à une date donnée"""
    schedule = get_schedule_by_date(date)
    if schedule and movie_id in schedule["movies"]:
        return schedule
    return None


def get_user_details(userid):
    """Récupère les détails d'un utilisateur depuis le service User"""
    try:
        response = requests.get(f"{USER_SERVICE_URL}/users/{userid}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def is_admin_user(userid):
    """Vérifie si l'utilisateur est un administrateur"""
    user_details = get_user_details(userid)
    if user_details and user_details.get('role') == 'admin':
        return True
    return False


# ============================================================================
# QUERY RESOLVERS
# ============================================================================

def all_bookings_resolver(obj, info, userid):
    """Récupère toutes les réservations (accès admin uniquement)"""
    if not userid:
        raise Exception("userid requis pour accéder aux réservations")
    
    if not is_admin_user(userid):
        raise Exception("Accès refusé - droits administrateur requis")
    
    bookings_list = list(collection.find({}))
    # Convertir ObjectId en string pour JSON
    for booking in bookings_list:
        if '_id' in booking:
            booking['_id'] = str(booking['_id'])
    return bookings_list


def bookings_by_user_resolver(obj, info, userid):
    """Récupère toutes les réservations d'un utilisateur"""
    booking = collection.find_one({"userid": userid})
    if booking and '_id' in booking:
        booking['_id'] = str(booking['_id'])
    return booking


def detailed_bookings_by_user_resolver(obj, info, userid):
    """Récupère les réservations détaillées d'un utilisateur avec infos des films et horaires"""
    user_booking = collection.find_one({"userid": userid})
    
    if not user_booking:
        return None
    
    detailed_bookings = []
    for date_entry in user_booking['dates']:
        date = date_entry['date']
        movies_details = []
        
        # Récupération du planning de la date
        schedule_details = get_schedule_by_date(date)
        
        # Récupération des détails pour chaque film réservé
        for movie_id in date_entry['movies']:
            movie_details = get_movie_details(movie_id)
            
            if movie_details and schedule_details:
                movies_details.append({
                    "movie": movie_details,
                    "schedule": schedule_details
                })
        
        if movies_details:
            detailed_bookings.append({
                "date": date,
                "movies": movies_details
            })
    
    return {
        "userid": userid,
        "bookings": detailed_bookings
    }


# ============================================================================
# MUTATION RESOLVERS
# ============================================================================

def create_booking_resolver(obj, info, input):
    """Créer une nouvelle réservation"""
    userid = input['userid']
    movieid = input['movieid']
    date = input['date']
    
    # Vérification de l'existence du film
    movie_details = get_movie_details(movieid)
    if not movie_details:
        raise Exception("Film non trouvé")
    
    # Vérification de la programmation du film
    schedule_details = get_schedule_details(movieid, date)
    if not schedule_details:
        raise Exception("Film non programmé à cette date")
    
    # Recherche ou création de l'utilisateur
    user_booking = collection.find_one({"userid": userid})
    
    if not user_booking:
        user_booking = {"userid": userid, "dates": []}
        collection.insert_one(user_booking)
    
    # Recherche ou création de la date
    date_entry = None
    date_index = -1
    for i, date_item in enumerate(user_booking['dates']):
        if date_item['date'] == date:
            date_entry = date_item
            date_index = i
            break
    
    if not date_entry:
        date_entry = {"date": date, "movies": []}
        user_booking['dates'].append(date_entry)
        date_index = len(user_booking['dates']) - 1
    
    # Vérification des doublons
    if movieid in date_entry['movies']:
        raise Exception("Film déjà réservé pour cette date")
    
    # Ajout de la réservation
    date_entry['movies'].append(movieid)
    user_booking['dates'][date_index] = date_entry
    collection.update_one(
        {"userid": userid},
        {"$set": {"dates": user_booking['dates']}}
    )
    
    return {
        "message": "Réservation créée avec succès",
        "booking": {
            "userid": userid,
            "movieid": movieid,
            "date": date
        }
    }


def delete_booking_resolver(obj, info, userid, movieid, date):
    """Supprimer une réservation spécifique"""
    booking = collection.find_one({"userid": userid})
    if not booking:
        raise Exception("Réservation non trouvée")
    
    updated_dates = []
    found = False
    for date_entry in booking['dates']:
        if date_entry['date'] == date and movieid in date_entry['movies']:
            found = True
            # Suppression du film de la réservation
            date_entry['movies'].remove(movieid)
            # Garder la date seulement si elle a encore des films
            if date_entry['movies']:
                updated_dates.append(date_entry)
        else:
            updated_dates.append(date_entry)
    
    if not found:
        raise Exception("Réservation non trouvée")
    
    # Mise à jour ou suppression de la réservation
    if not updated_dates:
        collection.delete_one({"userid": userid})
    else:
        collection.update_one(
            {"userid": userid},
            {"$set": {"dates": updated_dates}}
        )
    
    return {"message": "Réservation supprimée avec succès"}


def delete_all_user_bookings_resolver(obj, info, userid):
    """Supprimer toutes les réservations d'un utilisateur"""
    result = collection.delete_one({"userid": userid})
    if result.deleted_count == 0:
        raise Exception("Aucune réservation trouvée pour cet utilisateur")
    
    return {"message": f"Toutes les réservations de {userid} ont été supprimées"}


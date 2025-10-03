import json
import requests

# URLs des autres microservices
MOVIE_SERVICE_URL = "http://localhost:3001"  # Service Movie en GraphQL
SCHEDULE_SERVICE_URL = "http://localhost:3202"
USER_SERVICE_URL = "http://localhost:3203"

# Chargement de la base de données des réservations
with open('{}/data/bookings.json'.format("."), "r") as jsf:
    bookings = json.load(jsf)["bookings"]
    print("Réservations chargées:", len(bookings), "utilisateurs")


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def write_bookings_to_file(data):
    """Sauvegarde les données de réservations dans le fichier JSON"""
    with open('{}/data/bookings.json'.format("."), "w") as jsf:
        json.dump({"bookings": data}, jsf, indent=4)


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


def get_schedule_details(movie_id, date):
    """Récupère les détails d'un horaire depuis le service Schedule"""
    try:
        response = requests.get(f"{SCHEDULE_SERVICE_URL}/schedule/{movie_id}/{date}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
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
    
    return bookings


def bookings_by_user_resolver(obj, info, userid):
    """Récupère toutes les réservations d'un utilisateur"""
    for booking in bookings:
        if booking['userid'] == userid:
            return booking
    
    return None


def detailed_bookings_by_user_resolver(obj, info, userid):
    """Récupère les réservations détaillées d'un utilisateur avec infos des films et horaires"""
    user_booking = None
    for booking in bookings:
        if booking['userid'] == userid:
            user_booking = booking
            break
    
    if not user_booking:
        return None
    
    detailed_bookings = []
    for date_entry in user_booking['dates']:
        date = date_entry['date']
        movies_details = []
        
        # Récupération des détails pour chaque film réservé
        for movie_id in date_entry['movies']:
            movie_details = get_movie_details(movie_id)
            schedule_details = get_schedule_details(movie_id, date)
            
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
    user_booking = None
    for booking in bookings:
        if booking['userid'] == userid:
            user_booking = booking
            break
    
    if not user_booking:
        user_booking = {"userid": userid, "dates": []}
        bookings.append(user_booking)
    
    # Recherche ou création de la date
    date_entry = None
    for date_item in user_booking['dates']:
        if date_item['date'] == date:
            date_entry = date_item
            break
    
    if not date_entry:
        date_entry = {"date": date, "movies": []}
        user_booking['dates'].append(date_entry)
    
    # Vérification des doublons
    if movieid in date_entry['movies']:
        raise Exception("Film déjà réservé pour cette date")
    
    # Ajout de la réservation
    date_entry['movies'].append(movieid)
    write_bookings_to_file(bookings)
    
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
    for booking in bookings:
        if booking['userid'] == userid:
            for date_entry in booking['dates']:
                if date_entry['date'] == date and movieid in date_entry['movies']:
                    # Suppression du film de la réservation
                    date_entry['movies'].remove(movieid)
                    
                    # Suppression de la date si plus de films
                    if not date_entry['movies']:
                        booking['dates'].remove(date_entry)
                    
                    # Suppression de l'utilisateur si plus de dates
                    if not booking['dates']:
                        bookings.remove(booking)
                    
                    write_bookings_to_file(bookings)
                    return {"message": "Réservation supprimée avec succès"}
    
    raise Exception("Réservation non trouvée")


def delete_all_user_bookings_resolver(obj, info, userid):
    """Supprimer toutes les réservations d'un utilisateur"""
    for booking in bookings:
        if booking['userid'] == userid:
            bookings.remove(booking)
            write_bookings_to_file(bookings)
            return {"message": f"Toutes les réservations de {userid} ont été supprimées"}
    
    raise Exception("Aucune réservation trouvée pour cet utilisateur")


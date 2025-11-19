#!/usr/bin/env python3
"""
Script de test complet pour vérifier tous les services
"""
import requests
import json
import sys

# Configuration
USER_URL = "http://localhost:3203"
MOVIE_URL = "http://localhost:3001"
BOOKING_URL = "http://localhost:3201"

# Compteurs
tests_passed = 0
tests_failed = 0
errors = []

def test(name, func):
    """Exécute un test et compte les résultats"""
    global tests_passed, tests_failed
    try:
        result = func()
        if result:
            print(f"[OK] {name}")
            tests_passed += 1
            return True
        else:
            print(f"[FAIL] {name}")
            tests_failed += 1
            errors.append(name)
            return False
    except Exception as e:
        print(f"[FAIL] {name} - Erreur: {str(e)}")
        tests_failed += 1
        errors.append(f"{name}: {str(e)}")
        return False

# ============================================================================
# Tests User Service (REST)
# ============================================================================
print("\n" + "="*60)
print("TESTS USER SERVICE (REST)")
print("="*60)

def test_user_home():
    r = requests.get(f"{USER_URL}/")
    return r.status_code == 200 and "Welcome" in r.text

def test_user_get_all():
    r = requests.get(f"{USER_URL}/users")
    if r.status_code != 200:
        return False
    users = r.json()
    return isinstance(users, list) and len(users) > 0

def test_user_get_by_id():
    r = requests.get(f"{USER_URL}/users/chris_rivers")
    if r.status_code != 200:
        return False
    user = r.json()
    return user.get("id") == "chris_rivers" and user.get("role") == "admin"

def test_user_get_admin():
    r = requests.get(f"{USER_URL}/users/admin")
    if r.status_code != 200:
        return False
    admins = r.json()
    return isinstance(admins, list) and len(admins) > 0

test("User - Home", test_user_home)
test("User - Get All Users", test_user_get_all)
test("User - Get User By ID (chris_rivers)", test_user_get_by_id)
test("User - Get Admin Users", test_user_get_admin)

# ============================================================================
# Tests Movie Service (GraphQL)
# ============================================================================
print("\n" + "="*60)
print("TESTS MOVIE SERVICE (GraphQL)")
print("="*60)

def test_movie_home():
    r = requests.get(f"{MOVIE_URL}/")
    return r.status_code == 200 and "Welcome" in r.text

def test_movie_all():
    query = {"query": "query { all_movies { id title rating director } }"}
    r = requests.post(f"{MOVIE_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    return "data" in data and "all_movies" in data["data"] and len(data["data"]["all_movies"]) > 0

def test_movie_by_id():
    query = {"query": 'query { movie_by_id(id: "267eedb8-0f5d-42d5-8f43-72426b9fb3e6") { id title rating director } }'}
    r = requests.post(f"{MOVIE_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    return "data" in data and data["data"]["movie_by_id"] is not None

def test_movie_add_admin():
    import time
    # Utiliser un ID unique basé sur le timestamp
    unique_id = f"test-movie-{int(time.time())}"
    query = {
        "query": f'mutation {{ add_movie(movie: {{ id: "{unique_id}", title: "Nouveau Film Test", rating: 8.5, director: "Realisateur Test", author: "chris_rivers" }}) {{ message movie {{ id title }} }} }}'
    }
    r = requests.post(f"{MOVIE_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    # Vérifier qu'il n'y a pas d'erreur
    if "errors" in data:
        return False
    return "data" in data and "add_movie" in data["data"]

def test_movie_add_non_admin():
    query = {
        "query": 'mutation { add_movie(movie: { id: "test-movie-456", title: "Film Non Autorisé", rating: 5.0, director: "Test", author: "garret_heaton" }) { message movie { id title } } }'
    }
    r = requests.post(f"{MOVIE_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    # Doit retourner une erreur car garret_heaton n'est pas admin
    return "errors" in data and len(data["errors"]) > 0

test("Movie - Home", test_movie_home)
test("Movie - Get All Movies", test_movie_all)
test("Movie - Get Movie By ID", test_movie_by_id)
test("Movie - Add Movie (Admin) - ROUTE COMPLEXE", test_movie_add_admin)
test("Movie - Add Movie (Non-Admin) - Test Erreur", test_movie_add_non_admin)

# ============================================================================
# Tests Booking Service (GraphQL) - Routes Complexes
# ============================================================================
print("\n" + "="*60)
print("TESTS BOOKING SERVICE (GraphQL) - ROUTES COMPLEXES")
print("="*60)

def test_booking_home():
    r = requests.get(f"{BOOKING_URL}/")
    return r.status_code == 200 and "Bienvenue" in r.text

def test_booking_by_user():
    query = {"query": 'query { bookings_by_user(userid: "chris_rivers") { userid dates { date movies } } }'}
    r = requests.post(f"{BOOKING_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    return "data" in data

def test_booking_detailed():
    query = {
        "query": 'query { detailed_bookings_by_user(userid: "chris_rivers") { userid bookings { date movies { movie { id title rating director } schedule { date movies } } } } }'
    }
    r = requests.post(f"{BOOKING_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    return "data" in data

def test_booking_all_admin():
    query = {"query": 'query { all_bookings(userid: "chris_rivers") { userid dates { date movies } } }'}
    r = requests.post(f"{BOOKING_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    # Vérifier qu'il n'y a pas d'erreur (chris_rivers est admin)
    if "errors" in data:
        return False
    return "data" in data

def test_booking_all_non_admin():
    query = {"query": 'query { all_bookings(userid: "garret_heaton") { userid dates { date movies } } }'}
    r = requests.post(f"{BOOKING_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    # Doit retourner une erreur car garret_heaton n'est pas admin
    return "errors" in data and len(data["errors"]) > 0

def test_booking_create():
    # D'abord, supprimer la réservation si elle existe
    delete_query = {
        "query": 'mutation { delete_booking(userid: "garret_heaton", movieid: "267eedb8-0f5d-42d5-8f43-72426b9fb3e6", date: "20151201") { message } }'
    }
    requests.post(f"{BOOKING_URL}/graphql", json=delete_query)
    
    # Maintenant créer la réservation
    query = {
        "query": 'mutation { create_booking(input: { userid: "garret_heaton", movieid: "267eedb8-0f5d-42d5-8f43-72426b9fb3e6", date: "20151201" }) { message booking { userid movieid date } } }'
    }
    r = requests.post(f"{BOOKING_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    # Vérifier qu'il n'y a pas d'erreur
    if "errors" in data:
        return False
    return "data" in data and "create_booking" in data["data"]

test("Booking - Home", test_booking_home)
test("Booking - Get User Bookings", test_booking_by_user)
test("Booking - Detailed Bookings - ROUTE COMPLEXE", test_booking_detailed)
test("Booking - All Bookings (Admin) - ROUTE COMPLEXE", test_booking_all_admin)
test("Booking - All Bookings (Non-Admin) - Test Erreur", test_booking_all_non_admin)
test("Booking - Create Booking - ROUTE COMPLEXE", test_booking_create)

# ============================================================================
# Vérification MongoDB
# ============================================================================
print("\n" + "="*60)
print("VÉRIFICATION MONGODB")
print("="*60)

def test_mongodb_movies():
    # Vérifier via Movie service que les films sont en MongoDB
    query = {"query": "query { all_movies { id title } }"}
    r = requests.post(f"{MOVIE_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    movies = data.get("data", {}).get("all_movies", [])
    return len(movies) >= 7  # Au moins 7 films

def test_mongodb_users():
    # Vérifier via User service que les utilisateurs sont en MongoDB
    r = requests.get(f"{USER_URL}/users")
    if r.status_code != 200:
        return False
    users = r.json()
    return len(users) >= 7  # Au moins 7 utilisateurs

def test_mongodb_bookings():
    # Vérifier via Booking service que les réservations sont en MongoDB
    query = {"query": 'query { bookings_by_user(userid: "chris_rivers") { userid dates { date movies } } }'}
    r = requests.post(f"{BOOKING_URL}/graphql", json=query)
    if r.status_code != 200:
        return False
    data = r.json()
    # Même si pas de réservations, la requête doit fonctionner
    return "data" in data

test("MongoDB - Movies Collection", test_mongodb_movies)
test("MongoDB - Users Collection", test_mongodb_users)
test("MongoDB - Bookings Collection", test_mongodb_bookings)

# ============================================================================
# Résumé
# ============================================================================
print("\n" + "="*60)
print("RESUME DES TESTS")
print("="*60)
print(f"[OK] Tests reussis: {tests_passed}")
print(f"[FAIL] Tests echoues: {tests_failed}")
print(f"Total: {tests_passed + tests_failed}")

if errors:
    print("\n[FAIL] Erreurs detectees:")
    for error in errors:
        print(f"  - {error}")

if tests_failed == 0:
    print("\n[SUCCESS] TOUS LES TESTS SONT PASSES! Tout fonctionne correctement.")
    sys.exit(0)
else:
    print(f"\n[WARNING] {tests_failed} test(s) ont echoue. Verifiez les erreurs ci-dessus.")
    sys.exit(1)


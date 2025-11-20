import json
import os

from flask import Flask, jsonify, make_response, request
from pymongo import MongoClient

app = Flask(__name__)

PORT = 3203

PERSISTENCE_TYPE = os.getenv("PERSISTENCE_TYPE", "MONGODB")
JSON_FILE_PATH = '{}/data/users.json'.format(".")

# Connexion MongoDB
from urllib.parse import quote_plus
# Le mot de passe est encodé dans docker-compose.yml, sinon on utilise l'encodage par défaut
default_password = quote_plus("*65%8XPuGaQ#")
MONGO_URL = os.getenv("MONGO_URL", f"mongodb://root:{default_password}@localhost:27017/")

client = None
db = None
collection = None

if PERSISTENCE_TYPE == "MONGODB":
    # Connexion avec retry automatique (pymongo gère les reconnexions)
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client["users"]
    collection = db["users"]

    # Initialisation des données depuis JSON si la collection est vide
    if collection.count_documents({}) == 0:
        print("Initialisation de la base de données MongoDB avec les données JSON...")
        with open(JSON_FILE_PATH, "r") as jsf:
            users_data = json.load(jsf)["users"]
            if users_data:
                collection.insert_many(users_data)
                print(f"Utilisateurs chargés: {len(users_data)} utilisateurs")
    else:
        print(f"Base de données MongoDB déjà initialisée: {collection.count_documents({})} utilisateurs")
else:
    print(f"Utilisation de la persistance JSON (Fichier: {JSON_FILE_PATH})")

def get_json_data():
    try:
        with open(JSON_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": []}

def save_json_data(data):
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

@app.route("/", methods=['GET'])
def home():
    return "<h1 style='color:blue'>Welcome to the User service!</h1>"


@app.route("/users", methods=['GET'])
def get_users():
    if PERSISTENCE_TYPE == "MONGODB":
        users_list = list(collection.find({}))
        # Convertir ObjectId en string pour JSON
        for user in users_list:
            if '_id' in user:
                user['_id'] = str(user['_id'])
        return make_response(jsonify(users_list), 200)
    else:
        data = get_json_data()
        return make_response(jsonify(data.get("users", [])), 200)


@app.route("/users/<userid>", methods=['GET'])
def get_user_by_id(userid):
    if PERSISTENCE_TYPE == "MONGODB":
        user = collection.find_one({"id": str(userid)})
        if user is None:
            return make_response(jsonify({"error": "User ID not found"}), 404)
        
        if '_id' in user:
            user['_id'] = str(user['_id'])
        return make_response(jsonify(user), 200)
    else:
        data = get_json_data()
        for user in data.get("users", []):
            if user["id"] == str(userid):
                return make_response(jsonify(user), 200)
        return make_response(jsonify({"error": "User ID not found"}), 404)


@app.route("/users/admin", methods=['GET'])
def get_admin_users():
    if PERSISTENCE_TYPE == "MONGODB":
        admins = list(collection.find({"role": "admin"}))
        if len(admins) == 0:
            return make_response(jsonify({"error": "No admin users found"}), 204)
        
        # Convertir ObjectId en string pour JSON
        for admin in admins:
            if '_id' in admin:
                admin['_id'] = str(admin['_id'])
        return make_response(jsonify(admins), 200)
    else:
        data = get_json_data()
        admins = [u for u in data.get("users", []) if u.get("role") == "admin"]
        if len(admins) == 0:
            return make_response(jsonify({"error": "No admin users found"}), 204)
        return make_response(jsonify(admins), 200)


@app.route("/users", methods=['POST'])
def add_user():
    req = request.get_json()

    if PERSISTENCE_TYPE == "MONGODB":
        existing_user = collection.find_one({"id": str(req.get("id"))})
        if existing_user:
            return make_response(jsonify({"error": "User ID already exists"}), 400)

        collection.insert_one(req)
        if '_id' in req:
            req['_id'] = str(req['_id'])
        return make_response(jsonify(req), 201)
    else:
        data = get_json_data()
        users = data.get("users", [])
        for user in users:
            if user["id"] == str(req.get("id")):
                return make_response(jsonify({"error": "User ID already exists"}), 400)
        
        users.append(req)
        data["users"] = users
        save_json_data(data)
        return make_response(jsonify(req), 201)


@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
    req = request.get_json()
    
    if PERSISTENCE_TYPE == "MONGODB":
        user = collection.find_one({"id": str(userid)})
        if user is None:
            return make_response(jsonify({"error": "User ID not found"}), 404)

        # Exclure l'ID de la mise à jour pour éviter les conflits
        update_data = {k: v for k, v in req.items() if k != "id"}
        collection.update_one({"id": str(userid)}, {"$set": update_data})
        
        user = collection.find_one({"id": str(userid)})
        if '_id' in user:
            user['_id'] = str(user['_id'])
        return make_response(jsonify(user), 200)
    else:
        data = get_json_data()
        users = data.get("users", [])
        found = False
        updated_user = None
        
        for i, user in enumerate(users):
            if user["id"] == str(userid):
                found = True
                # Update fields
                for k, v in req.items():
                    if k != "id":
                        user[k] = v
                users[i] = user
                updated_user = user
                break
        
        if not found:
            return make_response(jsonify({"error": "User ID not found"}), 404)
            
        data["users"] = users
        save_json_data(data)
        return make_response(jsonify(updated_user), 200)


@app.route("/users/<userid>", methods=['DELETE'])
def delete_user(userid):
    if PERSISTENCE_TYPE == "MONGODB":
        user = collection.find_one({"id": str(userid)})
        if user is None:
            return make_response(jsonify({"error": "User ID not found"}), 404)

        collection.delete_one({"id": str(userid)})
        return make_response(jsonify({"message": "User deleted successfully"}), 200)
    else:
        data = get_json_data()
        users = data.get("users", [])
        found = False
        new_users = []
        
        for user in users:
            if user["id"] == str(userid):
                found = True
            else:
                new_users.append(user)
        
        if not found:
            return make_response(jsonify({"error": "User ID not found"}), 404)
            
        data["users"] = new_users
        save_json_data(data)
        return make_response(jsonify({"message": "User deleted successfully"}), 200)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)

from functools import wraps
from flask import request, jsonify, make_response
import os
import json
from pymongo import MongoClient
from urllib.parse import quote_plus


# https://flask.palletsprojects.com/en/stable/patterns/viewdecorators/
def admin_required():
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = request.headers.get("x-user-id")
            if not user_id:
                return make_response(jsonify({"error": "Unauthorized"}), 401)

            default_password = quote_plus("*65%8XPuGaQ#")
            PERSISTENCE_TYPE = os.getenv("PERSISTENCE_TYPE", "MONGODB")
            JSON_FILE_PATH = "{}/data/users.json".format(".")

            is_admin = False

            if PERSISTENCE_TYPE == "MONGODB":
                MONGO_URL = os.getenv(
                    "MONGO_URL", f"mongodb://root:{default_password}@localhost:27017/"
                )
                try:
                    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
                    db = client["users"]
                    collection = db["users"]
                    user = collection.find_one({"id": str(user_id)})
                    if user and user.get("role") == "admin":
                        is_admin = True
                    client.close()
                except Exception:
                    pass
            else:
                if os.path.exists(JSON_FILE_PATH):
                    try:
                        with open(JSON_FILE_PATH, "r") as json_file:
                            data = json.load(json_file)
                            for user in data.get("users", []):
                                if (
                                    user["id"] == str(user_id)
                                    and user.get("role") == "admin"
                                ):
                                    is_admin = True
                                    break
                    except Exception:
                        pass

            if not is_admin:
                return make_response(jsonify({"error": "Forbidden"}), 403)

            return f(*args, **kwargs)

        return decorated_function

    return wrapper

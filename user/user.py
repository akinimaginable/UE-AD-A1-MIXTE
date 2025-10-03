import json

from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

PORT = 3203

with open('{}/databases/users.json'.format("."), "r") as jsf:
    users = json.load(jsf)["users"]


def write_users_to_file(data):
    with open('{}/databases/users.json'.format("."), "w") as jsf:
        json.dump({"users": data}, jsf, indent=4)


@app.route("/", methods=['GET'])
def home():
    return "<h1 style='color:blue'>Welcome to the User service!</h1>"


@app.route("/users", methods=['GET'])
def get_users():
    return make_response(jsonify(users), 200)


@app.route("/users/<userid>", methods=['GET'])
def get_user_by_id(userid):
    user = next((user for user in users if str(user["id"]) == str(userid)), None)
    if user is None:
        return make_response(jsonify({"error": "User ID not found"}), 404)

    return make_response(jsonify(user), 200)


@app.route("/users/admin", methods=['GET'])
def get_admin_users():
    admins = [user for user in users if user.get("role") == "admin"]
    if len(admins) == 0:
        return make_response(jsonify({"error": "No admin users found"}), 204)

    return make_response(jsonify(admins), 200)


@app.route("/users", methods=['POST'])
def add_user():
    req = request.get_json()

    for user in users:
        if str(user["id"]) == str(req.get("id")):
            return make_response(jsonify({"error": "User ID already exists"}), 400)

    users.append(req)
    write_users_to_file(users)
    return make_response(jsonify(req), 201)


@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
    req = request.get_json()
    user = next((user for user in users if str(user["id"]) == str(userid)), None)
    if user is None:
        return make_response(jsonify({"error": "User ID not found"}), 404)

    user.update(req)
    write_users_to_file(users)
    return make_response(jsonify(user), 200)


@app.route("/users/<userid>", methods=['DELETE'])
def delete_user(userid):
    user = next((user for user in users if str(user["id"]) == str(userid)), None)
    if user is None:
        return make_response(jsonify({"error": "User ID not found"}), 404)

    users.remove(user)
    write_users_to_file(users)
    return make_response(jsonify({"message": "User deleted successfully"}), 200)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)

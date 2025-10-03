from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, QueryType, MutationType
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify, make_response

import resolvers as r

PORT = 3201
HOST = '0.0.0.0'
app = Flask(__name__)

# Chargement du schéma GraphQL
type_defs = load_schema_from_path('booking.graphql')

# Création des instances de types
query = QueryType()
mutation = MutationType()

# Liaison des résolveurs de requêtes
@query.field("all_bookings")
def resolve_all_bookings(obj, info, userid):
    return r.all_bookings_resolver(obj, info, userid)

@query.field("bookings_by_user")
def resolve_bookings_by_user(obj, info, userid):
    return r.bookings_by_user_resolver(obj, info, userid)

@query.field("detailed_bookings_by_user")
def resolve_detailed_bookings_by_user(obj, info, userid):
    return r.detailed_bookings_by_user_resolver(obj, info, userid)

# Liaison des résolveurs de mutations
@mutation.field("create_booking")
def resolve_create_booking(obj, info, input):
    return r.create_booking_resolver(obj, info, input)

@mutation.field("delete_booking")
def resolve_delete_booking(obj, info, userid, movieid, date):
    return r.delete_booking_resolver(obj, info, userid, movieid, date)

@mutation.field("delete_all_user_bookings")
def resolve_delete_all_user_bookings(obj, info, userid):
    return r.delete_all_user_bookings_resolver(obj, info, userid)

# Création du schéma exécutable
schema = make_executable_schema(type_defs, query, mutation)

# Message d'accueil
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Bienvenue dans le service Réservations GraphQL!</h1>", 200)

# Interface GraphQL Playground (pour tester dans le navigateur)
@app.route('/graphql', methods=['GET'])
def graphql_playground():
    return PLAYGROUND_HTML, 200

# Point d'entrée GraphQL
@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )
    status_code = 200 if success else 400
    return jsonify(result), status_code

if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)

from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify, make_response

import resolvers as r

PORT = 3001
HOST = '0.0.0.0'
app = Flask(__name__)

# Chargement du schéma GraphQL
type_defs = load_schema_from_path('movie.graphql')

# Création des instances de types
query = QueryType()
mutation = MutationType()

# Liaison des résolveurs de requêtes
@query.field("all_movies")
def resolve_all_movies(obj, info):
    return r.all_movies_resolver(obj, info)

@query.field("movie_by_id")
def resolve_movie_by_id(obj, info, id):
    return r.movie_by_id_resolver(obj, info, id)

@query.field("movie_by_title")
def resolve_movie_by_title(obj, info, title):
    return r.movie_by_title_resolver(obj, info, title)

# Liaison des résolveurs de mutations
@mutation.field("add_movie")
def resolve_add_movie(obj, info, movie):
    return r.add_movie_resolver(obj, info, movie)

@mutation.field("update_movie_rating")
def resolve_update_movie_rating(obj, info, id, rating, author):
    return r.update_movie_rating_resolver(obj, info, id, rating, author)

@mutation.field("delete_movie")
def resolve_delete_movie(obj, info, id, author):
    return r.delete_movie_resolver(obj, info, id, author)

# Création du schéma exécutable
schema = make_executable_schema(type_defs, query, mutation)

# Message d'accueil
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie GraphQL service!</h1>", 200)

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

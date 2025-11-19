import json
import os
from concurrent import futures

import grpc
from pymongo import MongoClient

import schedule_pb2
import schedule_pb2_grpc


class ScheduleServicer(schedule_pb2_grpc.ScheduleServicer):
    def __init__(self):
        # Connexion MongoDB
        from urllib.parse import quote_plus
        # Le mot de passe est encodé dans docker-compose.yml, sinon on utilise l'encodage par défaut
        default_password = quote_plus("*65%8XPuGaQ#")
        MONGO_URL = os.getenv("MONGO_URL", f"mongodb://root:{default_password}@localhost:27017/")
        # Connexion avec retry automatique (pymongo gère les reconnexions)
        self.client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        self.db = self.client["schedule"]
        self.collection = self.db["schedule"]
        
        # Initialisation des données depuis JSON si la collection est vide
        if self.collection.count_documents({}) == 0:
            print("Initialisation de la base de données MongoDB avec les données JSON...")
            with open('{}/data/times.json'.format("."), "r") as jsf:
                schedule_data = json.load(jsf)["schedule"]
                if schedule_data:
                    self.collection.insert_many(schedule_data)
                    print(f"Planning chargé: {len(schedule_data)} entrées")
        else:
            print(f"Base de données MongoDB déjà initialisée: {self.collection.count_documents({})} entrées")

    def GetAll(self, request, context):
        print(f"- running GetAll, request:({request})")
        schedule_list = []
        for entry in self.collection.find({}):
            schedule_list.append(schedule_pb2.DaySchedule(date=entry["date"], movies=entry["movies"]))
        return schedule_pb2.DayScheduleList(list=schedule_list)

    def GetByDate(self, request, context):
        print(f"- running GetByDate, request:({request})")
        result = []
        for entry in self.collection.find({"date": request.date}):
            result.append(schedule_pb2.DaySchedule(date=entry["date"], movies=entry["movies"]))
        if result:
            context.set_code(grpc.StatusCode.OK)
            context.set_details("Resource found")
            return schedule_pb2.DayScheduleList(list=result)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No movies scheduled that day")
            return schedule_pb2.DayScheduleList(list=[])

    def AddToSchedule(self, request, context):
        print(f"- running AddToSchedule, request:({request})")
        # check if the date already exists
        entry = self.collection.find_one({"date": request.date})
        if entry:
            if request.id not in entry["movies"]:
                entry["movies"].append(request.id)
                self.collection.update_one(
                    {"date": request.date},
                    {"$set": {"movies": entry["movies"]}}
                )
            context.set_code(grpc.StatusCode.OK)
            context.set_details("Resource added to schedule")
            return schedule_pb2.Empty()

        # if not, create it
        self.collection.insert_one({"date": request.date, "movies": [request.id]})
        context.set_code(grpc.StatusCode.OK)
        context.set_details("Resource added to schedule")
        return schedule_pb2.Empty()

    def RemoveFromSchedule(self, request, context):
        print(f"- running RemoveFromSchedule, request:({request})")
        entry = self.collection.find_one({"date": request.date})
        if entry:
            if request.id in entry["movies"]:
                entry["movies"].remove(request.id)
                if not entry["movies"]:
                    self.collection.delete_one({"date": request.date})
                else:
                    self.collection.update_one(
                        {"date": request.date},
                        {"$set": {"movies": entry["movies"]}}
                    )
                context.set_code(grpc.StatusCode.OK)
                context.set_details("Resource removed from schedule")
                return schedule_pb2.Empty()
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Movie is not scheduled that day")
                return schedule_pb2.Empty()

        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details("Date not found in schedule")
        return schedule_pb2.Empty()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    schedule_pb2_grpc.add_ScheduleServicer_to_server(ScheduleServicer(), server)
    server.add_insecure_port('[::]:3002')
    server.start()
    print("[Schedule/GRPC] service running on port 3002")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

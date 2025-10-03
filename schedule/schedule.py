import json
from concurrent import futures

import grpc
import schedule_pb2
import schedule_pb2_grpc


class ScheduleServicer(schedule_pb2_grpc.ScheduleServicer):
    def __init__(self):
        with open('{}/data/times.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["schedule"]
    
    def GetAll(self, request, context):
        """Retourne l'ensemble du planning"""
        schedule_list = []
        for day in self.db:
            schedule_list.append(
                schedule_pb2.DaySchedule(
                    date=day["date"],
                    movies=day["movies"]
                )
            )
        return schedule_pb2.DayScheduleList(schedule=schedule_list)
    
    def GetByDate(self, request, context):
        """Retourne le planning pour une date spécifique"""
        for day in self.db:
            if day["date"] == request.date:
                return schedule_pb2.DaySchedule(
                    date=day["date"],
                    movies=day["movies"]
                )
        # Si la date n'est pas trouvée, retourne un planning vide
        return schedule_pb2.DaySchedule(date=request.date, movies=[])
    
    def AddMovieToSchedule(self, request, context):
        """Ajoute un film au planning"""
        # TODO: Implémenter la logique d'ajout
        return schedule_pb2.IsOperationSuccessful(success=True)
    
    def RemoveMovieFromSchedule(self, request, context):
        """Supprime un film du planning"""
        # TODO: Implémenter la logique de suppression
        return schedule_pb2.IsOperationSuccessful(success=True)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    schedule_pb2_grpc.add_ScheduleServicer_to_server(ScheduleServicer(), server)
    server.add_insecure_port('[::]:3002')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

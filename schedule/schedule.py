import json
from concurrent import futures

import grpc

import schedule_pb2_grpc


class ScheduleServicer(schedule_pb2_grpc.ScheduleServicer):
    def __init__(self):
        with open('{}/data/times.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["schedule"]


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    schedule_pb2_grpc.add_ScheduleServicer_to_server(ScheduleServicer(), server)
    server.add_insecure_port('[::]:3002')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()

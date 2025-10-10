import json
from concurrent import futures

import grpc

import schedule_pb2
import schedule_pb2_grpc


class ScheduleServicer(schedule_pb2_grpc.ScheduleServicer):
    def __init__(self):
        with open('{}/data/times.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["schedule"]

    def save_db(self):
        with open('{}/data/times.json'.format("."), "w") as jsf:
            json.dump({"schedule": self.db}, jsf, indent=2)

    def GetAll(self, request, context):
        print(f"- running GetAll, request:({request})")
        schedule_list = [schedule_pb2.DaySchedule(date=entry["date"], movies=entry["movies"]) for entry in self.db]
        return schedule_pb2.DayScheduleList(list=schedule_list)

    def GetByDate(self, request, context):
        print(f"- running GetByDate, request:({request})")
        result = []
        for entry in self.db:
            if entry["date"] == request.date:
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
        for entry in self.db:
            if entry["date"] == request.date:
                entry["movies"].append(request.id)
                self.save_db()
                context.set_code(grpc.StatusCode.OK)
                context.set_details("Resource added to schedule")
                return schedule_pb2.Empty()

        # if not, create it
        self.db.append({"date": request.date, "movies": [request.id]})
        self.save_db()
        context.set_code(grpc.StatusCode.OK)
        context.set_details("Resource added to schedule")
        return schedule_pb2.Empty()

    def RemoveFromSchedule(self, request, context):
        print(f"- running RemoveFromSchedule, request:({request})")
        for entry in self.db:
            if entry["date"] == request.date:
                if request.id in entry["movies"]:
                    entry["movies"].remove(request.id)
                    if not entry["movies"]:
                        self.db.remove(entry)
                    self.save_db()
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

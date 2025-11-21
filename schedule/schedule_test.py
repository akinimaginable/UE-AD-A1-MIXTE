import grpc

import schedule_pb2
import schedule_pb2_grpc

# Test parameters
TEST_MOVIE_ID = "uwu"
TEST_DATE = "20151130"

channel = grpc.insecure_channel("localhost:3002")
stub = schedule_pb2_grpc.ScheduleStub(channel)


def get_all_test():
    print("\n--- Testing GetAll ---")
    all_movies = stub.GetAll(schedule_pb2.Empty())
    for entry in all_movies.list:
        print(f"Date: {entry.date}, Movies: {entry.movies}")


def get_by_date_test():
    print("\n--- Testing GetByDate ---")
    bydate_resp = stub.GetByDate(schedule_pb2.Date(date=TEST_DATE))
    print(bydate_resp)


def add_to_schedule_test():
    print("\n--- Testing AddToSchedule ---")
    stub.AddToSchedule(schedule_pb2.Movie(date=TEST_DATE, id=TEST_MOVIE_ID))
    print("Done!")


def remove_from_schedule_test():
    print("\n--- Testing RemoveMovieFromSchedule ---")
    stub.RemoveFromSchedule(schedule_pb2.Movie(date=TEST_DATE, id=TEST_MOVIE_ID))
    print("Done!")


if __name__ == "__main__":
    get_all_test()
    get_by_date_test()
    add_to_schedule_test()
    remove_from_schedule_test()

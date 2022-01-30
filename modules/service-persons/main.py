import time
from concurrent import futures
import os
from app import create_app
import asyncio

import grpc
import app.udaconnect.person_pb2_grpc as person_pb2_grpc
from app.udaconnect.services import KafkaPersonService, GrpcPersonService

app = create_app(os.getenv("FLASK_ENV") or "test")

if __name__ == "__main__":
    # Initialize gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    person_pb2_grpc.add_PersonServiceServicer_to_server(GrpcPersonService(), server)

    print("Server starting on port 5005...")
    server.add_insecure_port("[::]:5005")
    server.start()
    asyncio.run(KafkaPersonService.consumePersons())
    app.run(debug=True, port=5001)

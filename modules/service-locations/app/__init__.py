import grpc
from concurrent import futures
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
import os


from threading import Event
import signal

from flask_kafka import FlaskKafka


db = SQLAlchemy()
KAFKA_SERVER = os.getenv('KAFKA_SERVER') if os.getenv('KAFKA_SERVER') is not None else '127.0.0.1:9092'


INTERRUPT_EVENT = Event()

bus = FlaskKafka(INTERRUPT_EVENT,
                 bootstrap_servers=",".join([KAFKA_SERVER]),
                 group_id="consumer-locations"
                 )


def listen_kill_server():
    signal.signal(signal.SIGTERM, bus.interrupted_process)
    signal.signal(signal.SIGINT, bus.interrupted_process)
    signal.signal(signal.SIGQUIT, bus.interrupted_process)
    signal.signal(signal.SIGHUP, bus.interrupted_process)


@bus.handle('locations')
def persons_topic_handler(msg):
    #print("consumed {} from persons-topic".format(msg))
    from app.udaconnect.services import KafkaLocationService
    KafkaLocationService.consumeLocations(msg)


def create_app(env=None):
    from app.config import config_by_name
    from app.udaconnect.services import GrpcLocationService
    import app.udaconnect.location_pb2_grpc as location_pb2_grpc

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])
    api = Api(app, title="UdaConnect Location Service", version="0.1.0")

    CORS(app)  # Set CORS for development

    db.init_app(app)

    # Initialize gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    location_pb2_grpc.add_LocationServiceServicer_to_server(GrpcLocationService(), server)

    print("Server starting on port 5005...")
    server.add_insecure_port("[::]:5005")
    server.start()

    @app.route("/health")
    def health():
        return jsonify("healthy")

    return app

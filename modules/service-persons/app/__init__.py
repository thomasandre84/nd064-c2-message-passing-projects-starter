from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy

import grpc
from concurrent import futures
import app.udaconnect.person_pb2_grpc as person_pb2_grpc

from threading import Event
import signal

from flask_kafka import FlaskKafka

db = SQLAlchemy()

INTERRUPT_EVENT = Event()

bus = FlaskKafka(INTERRUPT_EVENT,
                 bootstrap_servers=",".join(["localhost:9092"]),
                 group_id="consumer-grp-id"
                 )


def listen_kill_server():
    signal.signal(signal.SIGTERM, bus.interrupted_process)
    signal.signal(signal.SIGINT, bus.interrupted_process)
    signal.signal(signal.SIGQUIT, bus.interrupted_process)
    signal.signal(signal.SIGHUP, bus.interrupted_process)


@bus.handle('persons')
def persons_topic_handler(msg):
    print("consumed {} from persons-topic".format(msg))


def create_app(env=None):
    from app.config import config_by_name
    from app.udaconnect.services import KafkaPersonService, GrpcPersonService

    app = Flask(__name__)
    app.config.from_object(config_by_name[env or "test"])
    api = Api(app, title="UdaConnect Person Service", version="0.1.0")

    CORS(app)  # Set CORS for development

    db.init_app(app)

    # Initialize gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    person_pb2_grpc.add_PersonServiceServicer_to_server(GrpcPersonService(), server)

    print("Server starting on port 5005...")
    server.add_insecure_port("[::]:5005")
    server.start()


    @app.route("/health")
    def health():
        return jsonify("healthy")

    bus.run()
    listen_kill_server()

    return app

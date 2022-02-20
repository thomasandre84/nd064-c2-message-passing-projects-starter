import logging
from datetime import datetime, timedelta
from typing import Dict, List

from app.udaconnect.schemas import LocationSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text
import os

import app.udaconnect.location_pb2_grpc as location_pb2_grpc
import app.udaconnect.location_pb2 as location_pb2
from json import dumps
import grpc
from kafka import KafkaProducer


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api-locations")

TOPIC_NAME = 'persons'
KAFKA_SERVER = os.getenv("KAFKA_SERVER") if os.getenv("KAFKA_SERVER") is not None else 'localhost:9092'

GRPC_CHANNEL = os.getenv('LOCATION_SERVICE')+":5005" if os.getenv('LOCATION_SERVICE') is not None else 'localhost:5005'


class LocationService:
    _producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER,
                              value_serializer=lambda x:
                              dumps(x).encode('utf-8'))
    _channel = grpc.insecure_channel(GRPC_CHANNEL)
    _stub = location_pb2_grpc.LocationServiceStub(channel=_channel)

    @staticmethod
    def retrieve(location_id) -> LocationSchema:
        id_message = location_pb2.LocationId(
            id=location_id
        )
        response = LocationService._stub.GetById(id_message)
        #print(response)
        schema = LocationSchema()
        location = schema.dump(response)
        return location

    @staticmethod
    def create(location: Dict) -> LocationSchema:
        validation_results: Dict = LocationSchema().validate(location)
        if validation_results:
            logger.warning(f"Unexpected data format in payload: {validation_results}")
            raise Exception(f"Invalid payload: {validation_results}")

        schema = LocationSchema()
        new_location = schema.dump(location)
        logger.info("Adding new Location {}".format(new_location))
        LocationService._producer.send(TOPIC_NAME, new_location)
        return new_location

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from json import loads

from app import db
from app.udaconnect.models import Connection, Location, Person
from app.udaconnect.schemas import ConnectionSchema, LocationSchema, PersonSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text
import app.udaconnect.location_pb2_grpc as location_pb2_grpc
import app.udaconnect.location_pb2 as location_pb2

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api")


class GrpcLocationService(location_pb2_grpc.LocationServiceServicer):

    def GetById(self, location_id):
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
            .filter(Location.id == location_id)
            .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        result = location_pb2.LocationMessage(**location)
        return result

    def GetByPersonId(self, person_id):
        location, coord_text = (
            db.session.query(Location, Location.coordinate.ST_AsText())
                .filter(Location.person_id == person_id)
                .one()
        )

        # Rely on database to return text form of point to reduce overhead of conversion in app code
        location.wkt_shape = coord_text
        result = location_pb2.LocationMessage(**location)
        return result


class KafkaLocationService:

    @staticmethod
    def consumeLocations(message):
        location = loads(message.value.decode('utf-8'))
        print(location)
        new_location = Location()
        new_location.person_id = location["person_id"]
        new_location.creation_time = location["creation_time"]
        new_location.coordinate = ST_Point(location["latitude"], location["longitude"])
        db.session.add(new_location)
        db.session.commit()


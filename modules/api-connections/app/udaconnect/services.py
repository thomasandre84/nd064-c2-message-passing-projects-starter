import logging
from datetime import datetime, timedelta
from typing import Dict, List
import os
from app.udaconnect.schemas import ConnectionSchema, LocationSchema, PersonSchema
from geoalchemy2.functions import ST_AsText, ST_Point
from sqlalchemy.sql import text

import app.udaconnect.location_pb2_grpc as location_pb2_grpc
import app.udaconnect.location_pb2 as location_pb2
import app.udaconnect.person_pb2_grpc as person_pb2_grpc
import app.udaconnect.person_pb2 as person_pb2
from json import dumps
import grpc


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api")

GRPC_LOCATION_CHANNEL = os.getenv('LOCATION_SERVICE')+":5005" if os.getenv('LOCATION_SERVICE') is not None else 'localhost:5005'
GRPC_PERSON_CHANNEL = os.getenv('PERSON_SERVICE')+":5005" if os.getenv('PERSON_SERVICE') is not None else 'localhost:5005'


def filter_times(locations_raw, end_date, start_Date):
    locations = list()
    for location in locations_raw:
        if location.creation_time < end_date and location.creation_time <= start_Date:
            locations.append(location)

    return locations

class ConnectionService:

    _channel_person = grpc.insecure_channel(GRPC_PERSON_CHANNEL)
    _stub_person = person_pb2_grpc.PersonServiceStub(channel=_channel_person)

    _channel_location = grpc.insecure_channel(GRPC_LOCATION_CHANNEL)
    _stub_location = location_pb2_grpc.LocationServiceStub(channel=_channel_location)

    @staticmethod
    def find_contacts(person_id: int, start_date: datetime, end_date: datetime, meters=5
    ) -> List[ConnectionSchema]:
        """
        Finds all Person who have been within a given distance of a given Person within a date range.

        This will run rather quickly locally, but this is an expensive method and will take a bit of time to run on
        large datasets. This is by design: what are some ways or techniques to help make this data integrate more
        smoothly for a better user experience for API consumers?
        """
        id_message = location_pb2.PersonId(
            id=person_id
        )
        response_locations = ConnectionService._stub_location.GetByPersonId(id_message)

        schema = LocationSchema()
        locations_raw = list()
        for location in response_locations.locations:
            locations_raw.append(schema.dump(location))

        locations = filter_times(locations_raw, end_date, start_date)
        #  Location.creation_time < end_date).filter(
        #    Location.creation_time >= start_date
        #).all()

        # Cache all users in memory for quick lookup
        person_map: Dict[str, Person] = {person.id: person for person in ConnectionService.retrieve_all_persons()}

        # Prepare arguments for queries
        data = []
        for location in locations:
            data.append(
                {
                    "person_id": person_id,
                    "longitude": location.longitude,
                    "latitude": location.latitude,
                    "meters": meters,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            )

        query = text(
            """
        SELECT  person_id, id, ST_X(coordinate), ST_Y(coordinate), creation_time
        FROM    location
        WHERE   ST_DWithin(coordinate::geography,ST_SetSRID(ST_MakePoint(:latitude,:longitude),4326)::geography, :meters)
        AND     person_id != :person_id
        AND     TO_DATE(:start_date, 'YYYY-MM-DD') <= creation_time
        AND     TO_DATE(:end_date, 'YYYY-MM-DD') > creation_time;
        """
        )
        result: List[ConnectionSchema] = []
        for line in tuple(data):
            for (
                exposed_person_id,
                location_id,
                exposed_lat,
                exposed_long,
                exposed_time,
            ) in db.engine.execute(query, **line):
                location = Location(
                    id=location_id,
                    person_id=exposed_person_id,
                    creation_time=exposed_time,
                )
                location.set_wkt_with_coords(exposed_lat, exposed_long)

                result.append(
                    Connection(
                        person=person_map[exposed_person_id], location=location,
                    )
                )

        return result

    @staticmethod
    def retrieve_all_persons():
        response = ConnectionService._stub_person.GetAll(person_pb2.Empty())
        schema = PersonSchema()
        persons = list()
        for person in response.persons:
            persons.append(schema.dump(person))
        return persons

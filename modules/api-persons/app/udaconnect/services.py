import logging
from typing import Dict, List
from json import dumps
import os
from kafka import KafkaProducer

from app.udaconnect.schemas import PersonSchema
import grpc
import app.udaconnect.person_pb2_grpc as person_pb2_grpc
import app.udaconnect.person_pb2 as person_pb2

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-api-persons")

TOPIC_NAME = 'persons'
KAFKA_SERVER = os.getenv("KAFKA_SERVER") if os.getenv("KAFKA_SERVER") is not None else 'localhost:9092'

GRPC_CHANNEL = os.getenv('PERSON_SERVICE')+":5005" if os.getenv('PERSON_SERVICE') is not None else 'localhost:5005'


class PersonService:
    _producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER,
                                 value_serializer=lambda x:
                                 dumps(x).encode('utf-8'))

    _channel = grpc.insecure_channel(GRPC_CHANNEL)
    _stub = person_pb2_grpc.PersonServiceStub(channel=_channel)

    @staticmethod
    def create(person: Dict) -> PersonSchema:
        schema = PersonSchema()
        new_person = schema.dump(person)
        logger.info("Adding new Person {}".format(new_person))
        PersonService._producer.send(TOPIC_NAME, new_person)
        return new_person

    @staticmethod
    def retrieve(person_id: int) -> PersonSchema:
        #person = db.session.query(Person).get(person_id)
        id_message = person_pb2.ID(
            id=person_id
        )
        response = PersonService._stub.GetById(id_message)
        print(response)
        return None

    @staticmethod
    def retrieve_all() -> List[PersonSchema]:
        response = PersonService._stub.GetAll(person_pb2.Empty())
        print(response)
        return None

    @staticmethod
    def retrieve_paged(start: int, amount: int) -> List[PersonSchema]:
        page_message = person_pb2.Paged(
            start=start,
            amount=amount
        )
        response = PersonService._stub.GetPaged(page_message)
        print(response)
        return None
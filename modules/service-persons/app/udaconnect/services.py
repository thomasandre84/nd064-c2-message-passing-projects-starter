import logging
import os
from typing import List
from kafka import KafkaConsumer
from json import loads

from app import db
from app.udaconnect.models import Person
import app.udaconnect.person_pb2_grpc as person_pb2_grpc
#import person_pb2_grpc

TOPIC_NAME = 'persons'
KAFKA_SERVER = os.getenv('KAFKA_SERVER') if os.getenv('KAFKA_SERVER') is not None else '127.0.0.1:9092'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-person-service")


class KafkaPersonService:
    _consumer = KafkaConsumer(TOPIC_NAME,
                              bootstrap_servers=[KAFKA_SERVER],
                              auto_offset_reset='earliest',
                              enable_auto_commit=True,
                              group_id='person-service',
                              value_deserializer=lambda x: loads(x.decode('utf-8')))

    @staticmethod
    def consumePersons():
        for message in KafkaPersonService._consumer:
            person = message.value
            print(person)
            new_person = Person()
            new_person.first_name = person["first_name"]
            new_person.last_name = person["last_name"]
            new_person.company_name = person["company_name"]
            db.session.add(new_person)
            db.session.commit()

    @staticmethod
    def stopConsuming():
        KafkaPersonService._consumer.close()


class GrpcPersonService(person_pb2_grpc.PersonServiceServicer):
    """@staticmethod
    def create(person: Dict) -> Person:
        new_person = Person()
        new_person.first_name = person["first_name"]
        new_person.last_name = person["last_name"]
        new_person.company_name = person["company_name"]

        db.session.add(new_person)
        db.session.commit()

        return new_person"""

    @staticmethod
    def retrieve(person_id: int) -> Person:
        person = db.session.query(Person).get(person_id)
        return person

    @staticmethod
    def retrieve_all() -> List[Person]:
        return db.session.query(Person).all()

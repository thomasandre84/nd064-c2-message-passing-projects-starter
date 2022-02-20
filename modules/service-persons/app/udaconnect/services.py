import logging
import os
from typing import List
from json import loads

from app import db
from app.udaconnect.models import Person
import app.udaconnect.person_pb2_grpc as person_pb2_grpc

TOPIC_NAME = 'persons'
KAFKA_SERVER = os.getenv('KAFKA_SERVER') if os.getenv('KAFKA_SERVER') is not None else '127.0.0.1:9092'

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("udaconnect-person-service")


class KafkaPersonService:

    @staticmethod
    def consumePersons(message):
        person = loads(message.value.decode('utf-8'))
        print(person)
        new_person = Person()
        new_person.first_name = person["first_name"]
        new_person.last_name = person["last_name"]
        new_person.company_name = person["company_name"]
        db.session.add(new_person)
        db.session.commit()


class GrpcPersonService(person_pb2_grpc.PersonServiceServicer):

    @staticmethod
    def retrieve(person_id: int):
        person = db.session.query(Person).get(person_id)
        return person

    @staticmethod
    def retrieve_all():
        return db.session.query(Person).all()

    @staticmethod
    def retrieve_paged(start: int, amount: int):
        persons = db.session.query(Person).order_by(Person.id).offset(start).yield_per(amount)

        return persons

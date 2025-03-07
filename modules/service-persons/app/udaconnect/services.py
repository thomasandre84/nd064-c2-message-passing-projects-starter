import logging
import os
from typing import List
from json import loads

from app import db
from app.udaconnect.models import Person
import app.udaconnect.person_pb2_grpc as person_pb2_grpc
import app.udaconnect.person_pb2 as person_pb2

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

    def GetById(self, request, context):
        person = db.session.query(Person).get(request.id)
        person_grpc = person_pb2.PersonMessage(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name,
            company_name=person.company_name
        )
        return person_grpc

    def GetAll(self, request, context):
        persons = db.session.query(Person).all()
        result = person_pb2.PersonMessageList()
        for person in persons:
            person_grpc = person_pb2.PersonMessage(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                company_name=person.company_name
            )
            result.append(person_grpc)

        return result

    def GetPaged(self, request, context):
        persons = db.session.query(Person).order_by(Person.id).offset(request.start).yield_per(request.amount)
        count = db.session.query(Person).count()
        pages = count / request.amount + 1
        page = request.start / request.amount + 1
        persons_grpc = person_pb2.PersonMessageList()
        for person in persons:
            person_grpc = person_pb2.PersonMessage(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                company_name=person.company_name
            )
            persons_grpc.append(person_grpc)

        result = person_pb2.PagedPersonMessageList(
            page=page,
            pages=pages,
            persons=persons_grpc
        )
        return result

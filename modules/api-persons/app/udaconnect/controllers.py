from app.udaconnect.schemas import PersonSchema
from app.udaconnect.services import PersonService
from flask import request, g, Response
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from typing import List


api = Namespace("UdaConnect", description="Persons")
# TODO: This needs better exception handling


@api.route("/persons")
class PersonsResource(Resource):
    @accepts(schema=PersonSchema)
    @responds(schema=PersonSchema)
    def post(self) -> PersonSchema:
        payload = request.get_json()
        new_person: PersonSchema = PersonService.create(payload)
        return new_person

    @responds(schema=PersonSchema, many=True)
    def get(self) -> List[PersonSchema]:
        persons: List[PersonSchema] = PersonService.retrieve_all()
        return persons


@api.route("/persons/<person_id>")
@api.param("person_id", "Unique ID for a given Person", _in="query")
class PersonResource(Resource):
    @responds(schema=PersonSchema)
    def get(self, person_id) -> PersonSchema:
        person: PersonSchema = PersonService.retrieve(person_id)
        return person


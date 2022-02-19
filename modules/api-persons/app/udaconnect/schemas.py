from dataclasses import dataclass

from marshmallow import Schema, fields


class PersonSchema(Schema):
    id = fields.Integer()
    first_name = fields.String()
    last_name = fields.String()
    company_name = fields.String()


class PersonsPaged(Schema):
    page = fields.Integer()
    pages = fields.Integer()
    persons = fields.List(fields.Nested(PersonSchema))

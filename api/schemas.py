from marshmallow import Schema, fields

class UserSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

class UserAuthSchema(Schema):
    token = fields.Str()

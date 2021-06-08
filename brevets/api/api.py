import os
import flask
from datetime import datetime
from flask import Flask, request, Response
from flask_restful import Resource, Api
from pymongo import MongoClient
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer \
                                  as Serializer, BadSignature, \
                                  SignatureExpired)

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetsdb

SECRET_KEY = 'test1234@#$'


# Helper functions
def csv_form(l, k):
    """Helper function for returning data in CSV format"""
    headers = list(l[0].keys())
    values = []
    val_str = ""
    num = k if k > 0 else len(l)

    for i in range(num):
        values.append(list(l[i].values()))
    for j in range(len(values)):
        val_str += ",".join(values[j])
        val_str += "\n"
    return ",".join(headers) + "\n" + val_str


def json_form(l, k):
    """Helper function for returning data in JSON format"""
    if k > 0:
        new_l = []
        for i in range(k):
            new_l.append(dict(l[i]))
        return flask.jsonify(new_l)
    return flask.jsonify(l)


def verify_auth_token(token):
    """Helper function to verify tokens"""
    s = Serializer(SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False
    except BadSignature:
        return False
    return True


# Create resources
class listAll(Resource):
    def get(self, dtype='json'):
        token = request.args.get('token')
        if not verify_auth_token(token):
            return Response(status=401)
        topk = int(request.args.get('top', default=-1))
        items = list(db.timestable.find({}, {'_id': 0, 'index': 0, 'km': 0, 'miles': 0, 'location': 0}))
        if dtype == 'csv':
            return csv_form(items, topk)
        return json_form(items, topk)


class listOpenOnly(Resource):
    def get(self, dtype='json'):
        token = request.args.get('token')
        if not verify_auth_token(token):
            return Response(status=401)
        topk = int(request.args.get('top', default=-1))
        items = list(db.timestable.find({}, {'_id': 0, 'index': 0, 'km': 0, 'miles': 0, 'location': 0, 'close': 0}))
        if dtype == 'csv':
            return csv_form(items, topk)
        return json_form(items, topk)


class listCloseOnly(Resource):
    def get(self, dtype='json'):
        token = request.args.get('token')
        if not verify_auth_token(token):
            return Response(status=401)
        topk = int(request.args.get('top', default=-1))
        items = list(db.timestable.find({}, {'_id': 0, 'index': 0, 'km': 0, 'miles': 0, 'location': 0, 'open': 0}))
        if dtype == 'csv':
            return csv_form(items, topk)
        return json_form(items, topk)


class register(Resource):
    def post(self, username, password):
        hashed = pwd_context.encrypt(password)
        if not pwd_context.verify(password, hashed):
            return Response(status=400)
        if db.userstable.find_one({'username': username}) or db.userstable.find_one({'password': hashed}):
            return Response(status=400)
        item = {
            'username': username,
            'password': hashed
        }
        db.userstable.insert_one(item)
        return Response(flask.jsonify(item), status=201)


class token(Resource):
    def get(self, username, password, expiration=600):
        hashed = pwd_context.encrypt(password)
        if not pwd_context.verify(password, hashed):
            return Response(status=400)
        if not db.userstable.find_one({'username': username}) or db.userstable.find_one({'password': hashed}):
            return Response(status=400)
        s = Serializer(SECRET_KEY, expires_in=expiration)
        token = s.dumps({'id': db.userstable.find_one({'username': username}, {'_id': 1}),
                         'username': username, 'datetime': datetime.now()})
        item = {
            'token': token,
            'duration': expiration
        }
        return flask.jsonify(item)


# Create routes
api.add_resource(listAll, '/listAll', '/listAll/<string:dtype>')
api.add_resource(listOpenOnly, '/listOpenOnly', '/listOpenOnly/<string:dtype>')
api.add_resource(listCloseOnly, '/listCloseOnly', '/listCloseOnly/<string:dtype>')
api.add_resource(register, '/register/<string:username>/<string:password>')
api.add_resource(token, '/token/<string:username>/<string:password>')


# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

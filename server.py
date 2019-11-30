#! /usr/bin/env python

from flask import Flask
from flask_restful import Resource, Api

import requests

lightServer = 'x.x.x.x'

app = Flask(__name__)
api = Api(app)

class LightState(Resource):
    def get(self, state):
        return "get " + state + " " + str(color)
        #r =requests.get(lightServer + "/")

class LightStateWithColor(Resource):
    def get(self, state, color):
        return "get " + state + " " + str(color)
        #r =requests.get(lightServer + "/")
        
api.add_resource(LightStateWithColor, '/<state>/<color>')
api.add_resource(LightState, '/<state>')


if __name__ == "__main__":
    app.run(debug=True)

import datetime
import decimal
import json
import uuid
import enum

from flask import Flask, g, request, jsonify


class Color(enum.Enum):
    RED = 1
    BLUE = 2

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({
        "resp": "HMAC_NOK",
        "dt": datetime.datetime.now(),
        "decimal": decimal.Decimal("5.83"),
        "uuid": uuid.uuid4(),
        "enum": Color.RED.name
    })

@app.after_request
def after_request(response):
    # cors
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers['Access-Control-Allow-Headers'] = "*"
    response.headers['Access-Control-Allow-Methods'] = "GET,POST,PUT,PATCH,OPTIONS,DELETE"

    return response


if __name__ == "__main__":
    app.run('0.0.0.0', 5000, debug=True)

from flask import Flask, Response, request, jsonify
import json
from pprint import pprint
import requests
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from . import myauth

MONGO_URL = f"mongodb+srv://nana:{os.environ['MONGOPASS']}" \
            f"@cluster0-fbhim.azure.mongodb.net/test?retryWrites=true&w=majority"

app = Flask(__name__)

pprint(dict(os.environ))

debug_mode = False if "PRODUCTION" in os.environ.keys() else True
access_token = os.environ["TOKEN_DEV"] if debug_mode else os.environ["TOKEN"]

client = MongoClient(MONGO_URL)
db: Database = client["seitokai"]
done_collection: Collection = db.done


@app.route("/", defaults={"path": ""}, methods=["GET"])
@app.route("/<path:path>", methods=["GET", "POST"])
def index(path):
    session = request.args.get('session', default='', type=str)

    if session == "":
        return jsonify({"status": "error", "error": "no session"})

    if not myauth.check_session_key(session):
        return jsonify({"status": "error", "error": "invalid session"})

    data = list(done_collection.find({}, {"_id": False}))

    # print(data)

    return jsonify({"status": "ok", "data": data})


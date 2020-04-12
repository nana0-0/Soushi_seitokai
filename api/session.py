from flask import Flask, Response, request, jsonify
from pprint import pprint
import os
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from . import myauth
from datetime import datetime

MONGO_URL = f"mongodb+srv://nana:{os.environ['MONGOPASS']}" \
            f"@cluster0-fbhim.azure.mongodb.net/test?retryWrites=true&w=majority"

app = Flask(__name__)

pprint(dict(os.environ))

debug_mode = False if "PRODUCTION" in os.environ.keys() else True
access_token = os.environ["TOKEN_DEV"] if debug_mode else os.environ["TOKEN"]

client = MongoClient(MONGO_URL)
db: Database = client["seitokai"]
done_collection: Collection = db.done


@app.route("/", defaults={"path": ""}, methods=["POST"])
@app.route("/<path:path>", methods=["POST"])
def index(path):
    try:
        password = request.form['password']
    except:
        return jsonify({"status": "error", "error": "no password"})

    if not myauth.check_password(password):
        return jsonify({"status": "error", "error": "invalid password"})

    return jsonify({"status": "ok", "session": myauth.create_session_key(datetime.now())})

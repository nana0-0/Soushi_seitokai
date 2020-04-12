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


def send(userid: str, content: str):
    res = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {access_token}"},
        json={
            "to": userid,
            "messages": [
                {
                    "type": "text",
                    "text": content
                },
            ]})
    print("response :", res, res.content)
    return res


@app.route("/", defaults={"path": ""}, methods=["POST"])
@app.route("/<path:path>", methods=["POST"])
def index(path):
    try:
        userid = request.form['userid']
        content = request.form['content']
        session = request.form['session']
    except:
        return jsonify({"status": "error", "error": "form error"})

    if session == "":
        return jsonify({"status": "error", "error": "no session"})

    if not myauth.check_session_key(session):
        return jsonify({"status": "error", "error": "invalid session"})

    res = send(userid, content)

    if res.status_code != 200:
        return jsonify({"status": "error", "error": "line error", "status_code": res.status_code, "content": res.text})

    done_collection.update_one({"userId": userid}, {"$set": {"replied": True}})
    print("updated")

    return jsonify({"status": "ok", "status_code": res.status_code, "content": res.text})

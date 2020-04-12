from flask import Flask, Response, request
import json
from pprint import pprint
import requests
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import re

MONGO_URL = f"mongodb+srv://nana:{os.environ['MONGOPASS']}" \
            f"@cluster0-fbhim.azure.mongodb.net/test?retryWrites=true&w=majority"

app = Flask(__name__)

pprint(dict(os.environ))

debug_mode = False if "PRODUCTION" in os.environ.keys() else True
access_token = os.environ["TOKEN_DEV"] if debug_mode else os.environ["TOKEN"]

flex = {}

# pprint([p for p in Path("./flex/").iterdir()])
for p in Path("./flex/").iterdir():
    # print(p.stem)
    with p.open() as f:
        try:
            data = json.load(f)
            flex[p.stem] = data
        except Exception as e:
            print(f"error at file {p}")
            raise e

client = MongoClient(MONGO_URL)
db: Database = client["seitokai"]
suggestion_collection: Collection = db.suggestion


def send(replyToken: str, content: dict):
    res = requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {access_token}"},
        json={
            "replyToken": replyToken,
            "messages": [
                {
                    "type": "flex",
                    "altText": "開いて確認してください",
                    "contents": content
                }
            ]})
    print("response :", res, res.content)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def index(path):
    try:
        body = request.get_json()
        events = body["events"]
        # pprint(events)

        for event in events:
            # if event["type"] != "message":
            #     continue

            replyToken: str = event["replyToken"]
            message_text: str = ""
            try:
                if event["message"]["type"] == "text":
                    message_text = event["message"]["text"]
            except:
                pass

            print()
            print(f"debug mode = {debug_mode}")
            if debug_mode:
                print("*****New Message*****")
                # pprint(dict(os.environ))
                try:
                    print(f'reply Token {replyToken}')
                    pprint(event["message"])
                    pprint(event["source"])
                except:
                    pprint(event)

            record: dict = suggestion_collection.find_one(
                {"userId": event["source"]["userId"]})

            if record is None:
                suggestion_collection.insert_one(
                    {"userId": event["source"]["userId"]})
                record = suggestion_collection.find_one(
                    {"userId": event["source"]["userId"]})

            if "want" not in record.keys():
                record["want"] = "userid"

            # ロジック

            # userid
            if record["want"] == "userid":
                if message_text == "書き込む":
                    record["want"] = "reply"
            # reply
            elif record["want"] == "reply":
                if message_text == "個人":
                    record["want"] = "gakunen"
                    record["reply"] = "個人"
                elif message_text == "タイムライン":
                    record["want"] = "anonymous"
                    record["reply"] = "タイムライン"

            # anonymous
            elif record["want"] == "anonymous":
                if message_text == "匿名":
                    record["anonymous"] = True
                    record["want"] = "suggestion"
                elif message_text == "個人情報":
                    record["anonymous"] = False
                    record["want"] = "gakunen"
            # gakunen
            elif record["want"] == "gakunen":
                if re.match(r"^[1-3]年$", message_text):
                    record["gakunen"] = message_text
                    record["want"] = "bunya"

            # bunya
            elif record["want"] == "bunya":
                if message_text == "デザイン":
                    record["want"] = "class_design"
                if message_text == "C組":
                    record["class"] = "C"
                    record["want"] = "number"
                if message_text == "D組":
                    record["class"] = "D"
                    record["want"] = "number"
                if message_text == "ビジネス":
                    record["want"] = "class_business"

            # class_design
            elif record["want"] == "class_design":
                if message_text == "A組":
                    record["class"] = "A"
                    record["want"] = "number"
                if message_text == "B組":
                    record["class"] = "B"
                    record["want"] = "number"
            # class_business
            elif record["want"] == "class_business":
                if message_text == "E組":
                    record["class"] = "E"
                    record["want"] = "number"
                if message_text == "F組":
                    record["class"] = "F"
                    record["want"] = "number"
            # number
            elif record["want"] == "number":
                if re.match("^([1-3][0-9])|[1-9]$", message_text):
                    record["number"] = int(message_text)
                    record["want"] = "name"
            # name
            elif record["want"] == "name":
                if message_text.strip() != "":
                    record["name"] = message_text.strip()
                    record["want"] = "check1"
            # check1
            elif record["want"] == "check1":
                if message_text == "続ける":
                    record["want"] = "suggestion"
                if message_text == "キャンセル":
                    record["want"] = "userid"
                    suggestion_collection.delete_one(
                        {"userId": event["source"]["userId"]})

            # suggestion
            elif record["want"] == "suggestion":
                if message_text.strip() != "":
                    record["suggestion"] = message_text.strip()
                    record["want"] = "check2"
            # check2
            elif record["want"] == "check2":
                if message_text == "続ける":
                    record["want"] = "done"
                if message_text == "書き直す":
                    record["want"] = "suggestion"
                if message_text == "キャンセル":
                    record["want"] = "userid"
                    suggestion_collection.delete_one(
                        {"userId": event["source"]["userId"]})

            content = flex[record["want"]]

            if record["want"] == "check1":
                content["body"]["contents"][1]["contents"][
                    0]["text"] = f"返信方法: {record['reply']}に返信"
                content["body"]["contents"][1]["contents"][
                    1]["text"] = f"　　学年: {record['gakunen']}"
                content["body"]["contents"][1]["contents"][
                    2]["text"] = f"　クラス: {record['class']}組"
                content["body"]["contents"][1]["contents"][
                    3]["text"] = f"　　番号: {record['number']}番"
                content["body"]["contents"][1]["contents"][
                    4]["text"] = f"　　名前: {record['name']}"

            if record["want"] == "check2":
                content["body"]["contents"][1]["contents"][
                    0]["text"] = f"意見: {record['suggestion']}"

            suggestion_collection.update_one(
                {"userId": event["source"]["userId"]}, {"$set": record})
            send(replyToken, content)

            if record["want"] == "done":
                db.done.insert_one(record)
                suggestion_collection.delete_one(
                    {"userId": event["source"]["userId"]})
    except:
        return Response(f"LINEからアクセスして下さい")

    return Response(f"OK", mimetype="text/html")

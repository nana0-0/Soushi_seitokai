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
from uuid import uuid4

MONGO_URL = f"mongodb+srv://nana:{os.environ['MONGOPASS']}" \
            f"@cluster0-fbhim.azure.mongodb.net/test?retryWrites=true&w=majority"

app = Flask(__name__)

pprint(dict(os.environ))

#テスト
debug_mode = "PRODUCTION" not in os.environ.keys()
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

#LINEプラットフォームを介して応答
def send(replyToken: str, content: dict):
    #LINEプラットフォームに送る
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
        #Webhookイベントを受け取る
        body = request.get_json()
        events = body["events"]  
        #Webhookイベントの中身を参照するfor文
        for event in events:      
            replyToken: str = event["replyToken"]
            #ユーザーから送られてきたテキストの初期化
            message_text: str = ""
            #ユーザーから送られてきたテキストがあった場合は代入する
            try:
                if event["message"]["type"] == "text":
                    message_text = event["message"]["text"]
            #ユーザーから送られてきたテキストがなかった場合はpass
            except:
                pass

            if debug_mode:
                print()
                print(f"debug mode = {debug_mode}")
                pprint(dict(os.environ))
                print("*****New Message*****")
                # pprint(dict(os.environ))
                try:
                    print(f'reply Token {replyToken}')
                    pprint(event["message"])
                    pprint(event["source"])
                except:
                    pprint(event)

            #userIdとWebhookイベントの中の"source"の中の"userId"と一致しているrecordを取り出す
            record: dict = suggestion_collection.find_one(
                {"userId": event["source"]["userId"]})

            #userIdの一致するrecordがなかった場合新しく作成してinsertする
            if record is None:
                suggestion_collection.insert_one(
                    {"userId": event["source"]["userId"]})
                record = suggestion_collection.find_one(
                    {"userId": event["source"]["userId"]})

            #wantがない場合はuserIdで初期化する
            if "want" not in record.keys():
                record["want"] = "userid"

            #recordのwantの中身がuseridだった場合
            if record["want"] == "userid":
                #ユーザーから送られてきたテキストが"書き込む"だった場合
                if message_text == "書き込む":
                    #wantの中身に"reply"を代入する
                    record["want"] = "reply"
                    #uuidを作成する
                    record["uuid"] = str(uuid4())

            #recordのwantの中身がreplyだった場合
            elif record["want"] == "reply":
                #ユーザーから送られてきたテキストが"個人"だった場合
                if message_text == "個人":
                    #wantの中身に"gakunen"を代入する
                    record["want"] = "gakunen"
                    #replyの中身に"個人"を代入する
                    record["reply"] = "個人"

                #ユーザーから送られてきたテキストが"タイムライン"だった場合
                elif message_text == "タイムライン":
                    #wantの中身に"anonymous"を代入する
                    record["want"] = "anonymous"
                    #replyの中身に "タイムライン"を代入する
                    record["reply"] = "タイムライン"

            #recordのwantの中身がanonymousだった場合
            elif record["want"] == "anonymous":
                #ユーザーから送られてきたテキストが"匿名"だった場合
                if message_text == "匿名":
                    #anonymousの中身に"True"を代入する
                    record["anonymous"] = True
                    #wantの中身に"suggestion"を代入する
                    record["want"] = "suggestion"

                #ユーザーから送られてきたテキストが"個人情報"だった場合
                elif message_text == "個人情報":
                    #anonymousの中身に"False"を代入する
                    record["anonymous"] = False
                    #wantの中身に"gakunen"を代入する
                    record["want"] = "gakunen"

            #recordのwantの中身がgakunenだった場合
            elif record["want"] == "gakunen":
                #ユーザーから送られてきたテキストが1~3年であった場合
                if re.match(r"^[1-3]年$", message_text):
                    #gakunenの中身にユーザーから送られてきたテキストを代入する
                    record["gakunen"] = message_text
                    #wantの中身に"bunya"を代入する
                    record["want"] = "bunya"

            #recordのwantの中身がbunyaだった場合
            elif record["want"] == "bunya":
                #ユーザーから送られてきたテキストがデザインだった場合
                if message_text == "デザイン":
                    #wantの中身に"class_design"を代入する
                    record["want"] = "class_design"

                #ユーザーから送られてきたテキストがC組だった場合
                if message_text == "C組":
                    #classの中身にCを代入する
                    record["class"] = "C"
                    #wantの中身に"number"を代入する
                    record["want"] = "number"

                #ユーザーから送られてきたテキストがD組だった場合
                if message_text == "D組":
                    #classの中身にDを代入する
                    record["class"] = "D"
                    #wantの中身に"number"を代入する
                    record["want"] = "number"

                #ユーザーから送られてきたテキストがビジネスだった場合
                if message_text == "ビジネス":
                    #wantの中身に"class_business"を代入する
                    record["want"] = "class_business"

            #recordのwantの中身がclass_designだった場合
            elif record["want"] == "class_design":
                #ユーザーから送られてきたテキストがA組だった場合
                if message_text == "A組":
                    #classの中身にAを代入する
                    record["class"] = "A"
                    #wantの中身に"number"を代入する
                    record["want"] = "number"

                #ユーザーから送られてきたテキストがB組だった場合
                if message_text == "B組":
                    #classの中身にBを代入する
                    record["class"] = "B"
                    #wantの中身に"number"を代入する
                    record["want"] = "number"

            #recordのwantの中身がclass_businessだった場合
            elif record["want"] == "class_business":
                #ユーザーから送られてきたテキストがE組だった場合
                if message_text == "E組":
                    #classの中身にEを代入する
                    record["class"] = "E"
                    #wantの中身に"number"を代入する
                    record["want"] = "number"

                #ユーザーから送られてきたテキストがF組だった場合
                if message_text == "F組":
                    #classの中身にFを代入する
                    record["class"] = "F"
                    #wantの中身に"number"を代入する
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

            #個人情報の確認
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

            #意見の確認
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

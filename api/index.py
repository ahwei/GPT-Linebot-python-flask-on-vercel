from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent,LocationSendMessage, TextMessage, TextSendMessage, FlexSendMessage
from api.chatgpt import ChatGPT

import json
import os
import re

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

app = Flask(__name__)
chatgpt = ChatGPT()

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.message.type != "text":
        return

    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return
    
    if event.message.text == "地圖":
        working_status = True

        location_message = LocationSendMessage(
            title='my location',
            address='Taiwan',
            latitude=25.0409168,
            longitude=121.5639799)
        line_bot_api.reply_message(
            event.reply_token,
            [location_message,location_message])
        return

    if event.message.text == "卡片":
        working_status = True
        FlexMessage = json.load(open('./api/location.json','r',encoding='utf-8'))
        line_bot_api.reply_message(event.reply_token, FlexSendMessage('profile',FlexMessage))
        return
     

    if event.message.text == "閉嘴":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return

    if working_status:
        reply = [TextSendMessage(text=reply_msg)]
        try:                    
            chatgpt.add_msg(f"你非常愛護動物，你會站在動物的立場為他著想，並且只會回答寵物相關問題，以下是我的問題:{event.message.text}?\n")
            reply_msg = chatgpt.get_response().replace("AI:", "", 1)
            chatgpt.add_msg(f"AI:{reply_msg}\n")
            reply.append(TextSendMessage(text=reply_msg))
        except:                   
            reply.append(TextSendMessage(text='超過GPT使用次數，請稍後再試。'))

       

        

        if re.search('獸醫|動物醫療中心|寵物診所|獸醫診所|醫療', reply_msg):
            locationMessage = json.load(open('./api/location.json','r',encoding='utf-8'))
            reply.append(FlexSendMessage('profile', locationMessage))

        if re.search('公園|運動|跑步|心情', reply_msg):
            parkMessage = json.load(open('./api/park.json','r',encoding='utf-8'))
            reply.append(FlexSendMessage('profile', parkMessage))

        if re.search('寵物用品|寵物食品|寵物玩具|寵物保健|寵物美容|飲食|用品|用具', reply_msg):
            shopMessage = json.load(open('./api/shop.json','r',encoding='utf-8'))
            reply.append(FlexSendMessage('profile', shopMessage))


        line_bot_api.reply_message(
            event.reply_token,
            reply)


if __name__ == "__main__":
    app.run()

from flask import Flask, request, abort
import os
import openai

from linebot.v3.messaging import (
    Configuration,
    MessagingApi,
    ApiClient,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError

# 初始化 Flask
app = Flask(__name__)

# 環境變數
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# 設定 LINE API
configuration = Configuration(access_token=channel_access_token)
parser = WebhookParser(channel_secret)

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        for event in events:
            if event.type == "message" and event.message.type == "text":
                user_message = event.message.text

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_message}]
                )
                reply_text = response.choices[0].message.content.strip()

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )

    return "OK", 200  # 回傳 200 OK，LINE 才會通過 Webhook 驗證！

# 開放 port 給 Render 使用
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

"""
飞书AI机器人 - Matrix Agent
"""

import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 配置
APP_ID = "cli_a92ad4feddf8dcb5"
APP_SECRET = "F8n3V1f2I2IJiXrKcuxQpdqvRNQDHtOF"
MINIMAX_API_KEY = "sk-api-Wz0wLNNwNH2z1uwnOJ7TN2-R-E8z6gmnvldyNGX7LUk6JAfWkYW_TypGTyTbWmkr8tfoDTEHWTNi_fQGBAf7ZbCw644m9EKQPb5VCc5Zaz8Zrx-GPjUADQo"
MINIMAX_MODEL = "abab6.5s-chat"

def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    response = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET})
    result = response.json()
    return result.get("tenant_access_token") if result.get("code") == 0 else None

def reply_message(message_id, content, token):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    requests.post(url, headers=headers, json={"msg_type": "text", "content": json.dumps({"text": content})})

def chat_with_minimax(text):
    try:
        response = requests.post(
            "https://api.minimax.chat/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
            json={"model": MINIMAX_MODEL, "messages": [{"role": "user", "content": text}], "tokens_to_generate": 500},
            timeout=30
        )
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return "AI暂时无法回复"
    except Exception as e:
        return f"错误: {str(e)}"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if "challenge" in request.args:
            return jsonify({"challenge": request.args.get("challenge")})
        return jsonify({"code": 0})
    
    data = request.json
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    
    token = get_tenant_access_token()
    if not token:
        return jsonify({"code": 1, "msg": "token获取失败"})
    
    event = data.get("event", {})
    if event.get("type") == "message":
        msg_id = event.get("message_id")
        content = json.loads(event.get("content", "{}"))
        text = content.get("text", "").strip()
        
        if text:
            reply = chat_with_minimax(text)
            reply_message(msg_id, reply, token)
    
    return jsonify({"code": 0})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

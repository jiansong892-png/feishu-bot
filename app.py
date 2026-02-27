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
    print(f"Token响应: {result}")
    return result.get("tenant_access_token") if result.get("code") == 0 else None

def reply_message(message_id, text, token):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"msg_type": "text", "content": json.dumps({"text": text})}
    resp = requests.post(url, headers=headers, json=payload)
    print(f"回复响应: {resp.status_code} - {resp.text}")

def chat_with_minimax(text):
    try:
        resp = requests.post(
            "https://api.minimax.chat/v1/text/chatcompletion_v2",
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
            json={"model": MINIMAX_MODEL, "messages": [{"role": "user", "content": text}]},
            timeout=30
        )
        result = resp.json()
        print(f"AI响应: {result}")
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        return "AI暂时无法回复"
    except Exception as e:
        print(f"AI错误: {e}")
        return f"错误: {e}"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            return jsonify({"challenge": challenge})
        return jsonify({"code": 0})
    
    data = request.json
    print(f"收到: {json.dumps(data)}")
    
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})
    
    token = get_tenant_access_token()
    if not token:
        print("获取token失败")
        return jsonify({"code": 1, "msg": "token失败"})
    
    event = data.get("event", {})
    if event.get("type") == "message":
        msg_id = event.get("message_id")
        msg_type = event.get("message_type")
        content = event.get("content", "{}")
        
        if isinstance(content, str):
            content = json.loads(content)
        
        text = content.get("text", "").strip()
        print(f"消息ID: {msg_id}, 类型: {msg_type}, 内容: {text}")
        
        if text:
            reply = chat_with_minimax(text)
            reply_message(msg_id, reply, token)
            print(f"已回复: {reply}")
    
    return jsonify({"code": 0})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

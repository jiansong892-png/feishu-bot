"""
飞书AI机器人 - Matrix Agent
功能：接收飞书消息，调用MiniMax AI回复用户
"""

import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================== 配置区域 ====================
# 飞书应用凭据
APP_ID = "cli_a92ad4feddf8dcb5"
APP_SECRET = "F8n3V1f2I2IJiXrKcuxQpdqvRNQDHtOF"

# MiniMax API 配置
MINIMAX_API_KEY = "sk-api-Wz0wLNNwNH2z1uwnOJ7TN2-R-E8z6gmnvldyNGX7LUk6JAfWkYW_TypGTyTbWmkr8tfoDTEHWTNi_fQGBAf7ZbCw644m9EKQPb5VCc5Zaz8Zrx-GPjUADQo"
MINIMAX_MODEL = "abab6.5s-chat"

# ==================== 飞书API ====================
def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {"app_id": APP_ID, "app_secret": APP_SECRET}
    response = requests.post(url, json=data)
    result = response.json()
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        print(f"获取token失败: {result}")
        return None   

def reply_message(message_id, message_type, content, token):
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
    data = {"msg_type": message_type, "content": json.dumps(content)}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# ==================== MiniMax AI对话 ====================
def chat_with_minimax(user_message):
    try:
        url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MINIMAX_MODEL,
            "messages": [{"role": "user", "content": user_message}],
            "tokens_to_generate": 1024,
            "temperature": 0.7,
            "top_p": 0.95
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "抱歉，AI暂时无法回复"
    except Exception as e:
        return f"抱歉，发生了错误: {str(e)}"

# ==================== 消息处理 ====================
@app.route("/webhook", methods=["GET", "POST"])
def handle_webhook():
    # 处理GET请求（飞书验证URL时）
    if request.method == "GET":
        args = request.args
        if "challenge" in args:
            return jsonify({"challenge": args.get("challenge")})
        return jsonify({"code": 0, "msg": "ok"})
    
    # POST请求 - 处理消息事件
    token = get_tenant_access_token()
    if not token:
        return jsonify({"code": 1, "msg": "获取token失败"})

    event_data = request.json
    event_type = event_data.get("event", {}).get("type")
    if event_type == "message":
        message = event_data.get("event", {})
        message_id = message.get("message_id")
        message_type = message.get("message_type")
        
        if message_type == "text":
            content = json.loads(message.get("content", "{}"))
            user_text = content.get("text", "")
            ai_reply = chat_with_minimax(user_text)
            reply_message(message_id, "text", {"text": ai_reply}, token)
            return jsonify({"code": 0, "msg": "success"})
        else:
            reply_message(message_id, "text", {"text": "抱歉，我目前只能处理文字消息"}, token)
            return jsonify({"code": 0, "msg": "success"})

    return jsonify({"code": 0, "msg": "ok"})

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

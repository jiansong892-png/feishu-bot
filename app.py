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
# 请替换为你自己的API Key
MINIMAX_API_KEY = "sk-api-Wz0wLNNwNH2z1uwnOJ7TN2-R-E8z6gmnvldyNGX7LUk6JAfWkYW_TypGTyTbWmkr8tfoDTEHWTNi_fQGBAf7ZbCw644m9EKQPb5VCc5Zaz8Zrx-GPjUADQo"

# MiniMax 模型名称
# 可选: abab6.5s-chat, abab6.5g-chat, abab6-chat 等
MINIMAX_MODEL = "abab6.5s-chat"

# ==================== 飞书API ====================
def get_tenant_access_token():
    """获取tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    response = requests.post(url, json=data)
    result = response.json()
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        print(f"获取token失败: {result}")
        return None

def reply_message(message_id, message_type, content, token):
    """回复消息"""
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "msg_type": message_type,
        "content": json.dumps(content)
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# ==================== MiniMax AI对话 ====================
def chat_with_minimax(user_message):
    """调用MiniMax API获取回复"""
    try:
        url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MINIMAX_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "tokens_to_generate": 1024,
            "temperature": 0.7,
            "top_p": 0.95
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()
        
        print(f"MiniMax API响应: {json.dumps(result, ensure_ascii=False)}")
        
        # 检查返回是否包含回复
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
            return reply
        elif "base_resp" in result:
            return f"API错误: {result.get('base_resp', {}).get('status_msg', '未知错误')}"
        else:
            return "抱歉，AI暂时无法回复，请稍后再试"
            
    except Exception as e:
        print(f"MiniMax调用失败: {e}")
        return f"抱歉，发生了错误: {str(e)}"

# ==================== 消息处理 ====================
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """处理飞书消息回调"""
    # 获取token
    token = get_tenant_access_token()
    if not token:
        return jsonify({"code": 1, "msg": "获取token失败"})

    # 解析飞书推送的数据
    event_data = request.json
    print(f"收到飞书消息: {json.dumps(event_data, ensure_ascii=False)}")

    # 处理验证URL（飞书首次配置时）
    if "challenge" in event_data:
        return jsonify({"challenge": event_data["challenge"]})

    # 处理消息事件
    event_type = event_data.get("event", {}).get("type")
    if event_type == "message":
        message = event_data.get("event", {})
        message_id = message.get("message_id")
        sender_id = message.get("sender", {}).get("user_id", {}).get("open_id")
        message_type = message.get("message_type")
        
        # 获取消息内容
        if message_type == "text":
            content = json.loads(message.get("content", "{}"))
            user_text = content.get("text", "")
            
            # 调用MiniMax AI获取回复
            ai_reply = chat_with_minimax(user_text)
            
            # 回复用户
            reply_message(message_id, "text", {"text": ai_reply}, token)
            
            return jsonify({"code": 0, "msg": "success"})
        else:
            # 非文本消息，发送提示
            reply_message(message_id, "text", {"text": "抱歉，我目前只能处理文字消息"}, token)
            return jsonify({"code": 0, "msg": "success"})

    return jsonify({"code": 0, "msg": "ok"})

@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

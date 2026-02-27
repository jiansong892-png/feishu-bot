# 获取token
    token = get_tenant_access_token()
    if not token:
        return jsonify({"code": 1, "msg": "获取token失败"})

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

import requests
import time
import os
from datetime import datetime

# 配置
BILIBILI_UID = "1856426471"
WXPUSHER_APP_TOKEN = "AT_kbhm0sEGtix10zbJB3B5dxNxw8fIRXbq"
WXPUSHER_TOPIC_ID = "45630"

# 状态文件
STATE_FILE = "last_dynamic.txt"

def get_user_dynamics():
    """获取B站用户动态"""
    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={BILIBILI_UID}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if data.get("code") == 0 and data.get("data", {}).get("items"):
            return data["data"]["items"][0]
        return None
    except Exception as e:
        print(f"获取动态失败: {e}")
        return None

def send_wxpusher(title, content):
    """发送微信推送"""
    url = "https://wxpusher.zjiecode.com/api/send/message"
    data = {
        "appToken": WXPUSHER_APP_TOKEN,
        "content": content,
        "summary": title,
        "contentType": 1,
        "topicIds": [int(WXPUSHER_TOPIC_ID)],
        "url": f"https://space.bilibili.com/{BILIBILI_UID}/dynamic"
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        result = resp.json()
        if result.get("code") == 1000:
            print(f"✅ 推送成功: {title}")
        else:
            print(f"❌ 推送失败: {result}")
    except Exception as e:
        print(f"❌ 推送异常: {e}")

def get_last_dynamic_id():
    """读取上次动态ID"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None

def save_dynamic_id(dynamic_id):
    """保存动态ID"""
    with open(STATE_FILE, "w") as f:
        f.write(str(dynamic_id))

def main():
    print(f"[{datetime.now()}] 开始检查动态...")
    
    dynamic = get_user_dynamics()
    if not dynamic:
        print("未获取到动态")
        return
    
    dynamic_id = dynamic.get("id_str")
    last_id = get_last_dynamic_id()
    
    if last_id is None:
        # 首次运行，只记录ID不推送
        save_dynamic_id(dynamic_id)
        print(f"初始化完成，当前动态ID: {dynamic_id}")
        return
    
    if dynamic_id != last_id:
        # 有新动态
        modules = dynamic.get("modules", {})
        author = modules.get("module_author", {}).get("name", "UP主")
        
        # 提取动态内容
        desc = modules.get("module_dynamic", {}).get("desc", {}).get("text", "")
        major = modules.get("module_dynamic", {}).get("major", {})
        
        content_parts = []
        if desc:
            content_parts.append(desc[:200])
        
        # 检查是否有视频/图片等
        if major.get("type") == "MAJOR_TYPE_ARCHIVE":
            video = major.get("archive", {})
            content_parts.append(f"\n📹 视频: {video.get('title', '')}")
        elif major.get("type") == "MAJOR_TYPE_DRAW":
            content_parts.append(f"\n🖼️ 发布了图片动态")
        
        title = f"{author} 发布了新动态"
        content = "\n".join(content_parts) if content_parts else "发布了新动态"
        
        send_wxpusher(title, content)
        save_dynamic_id(dynamic_id)
        print(f"✅ 检测到新动态: {dynamic_id}")
    else:
        print(f"无新动态 (当前ID: {dynamic_id})")

if __name__ == "__main__":
    main()

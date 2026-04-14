from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import urllib
import time
import sqlite3
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 前端目录（相对于 backend 的上一级）
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# ===== 托管前端静态文件 =====
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def frontend_files(filename):
    # API 路由不走这里
    if filename.startswith('api/'):
        return jsonify({"code": 404, "message": "Not Found"}), 404
    return send_from_directory(FRONTEND_DIR, filename)

# 数据库配置
DATABASE = 'music_history.db'

def init_db():
    """初始化数据库，创建歌曲记录表"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS music_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            prompt TEXT,
            lyrics TEXT,
            audio_url TEXT,
            cover_url TEXT,
            duration INTEGER,
            music_type TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("数据库初始化完成")

def save_music_record(music_data):
    """保存音乐记录到数据库"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO music_history 
            (title, prompt, lyrics, audio_url, cover_url, duration, music_type, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            music_data.get('title', ''),
            music_data.get('prompt', ''),
            music_data.get('lyrics', ''),
            music_data.get('audio_url', ''),
            music_data.get('cover_url', ''),
            music_data.get('duration', 0),
            music_data.get('music_type', ''),
            music_data.get('source', '')
        ))
        
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        return record_id
    except Exception as e:
        print(f"保存音乐记录失败: {str(e)}")
        return None

def get_music_history(limit=50):
    """获取音乐历史记录"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, prompt, lyrics, audio_url, cover_url, 
                   duration, music_type, source, created_at
            FROM music_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        
        # 转换为字典列表
        history = []
        for record in records:
            history.append({
                'id': record[0],
                'title': record[1],
                'prompt': record[2],
                'lyrics': record[3],
                'audio_url': record[4],
                'cover_url': record[5],
                'duration': record[6],
                'music_type': record[7],
                'source': record[8],
                'created_at': record[9]
            })
        return history
    except Exception as e:
        print(f"获取历史记录失败: {str(e)}")
        return []

def delete_music_record(record_id):
    """删除音乐记录"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM music_history WHERE id = ?', (record_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"删除音乐记录失败: {str(e)}")
        return False

# 快速歌词生成（避免API调用延迟）
def generate_fast_lyrics(theme):
    """基于主题快速生成中文歌词模板"""
    
    # 根据主题选择关键词
    theme_keywords = {
        '爱': ('爱情', '心跳', '永恒', '甜蜜'),
        '情': ('感情', '温柔', '深情', '眷恋'),
        '梦': ('梦想', '追逐', '星空', '远方'),
        '夜': ('夜晚', '星光', '寂静', '思念'),
        '雨': ('雨滴', '忧伤', '回忆', '等待'),
        '海': ('海洋', '波涛', '自由', '辽阔'),
        '钱': ('财富', '成功', '奋斗', '荣耀'),
        '富': ('富裕', '梦想', '努力', '收获'),
        '春': ('春天', '花开', '希望', '新生'),
        '夏': ('夏天', '阳光', '热情', '活力'),
        '秋': ('秋天', '落叶', '思念', '收获'),
        '冬': ('冬天', '雪花', '温暖', '守候'),
    }
    
    # 找到匹配的关键词
    keywords = ('梦想', '希望', '未来', '光芒')  # 默认
    for key, words in theme_keywords.items():
        if key in theme:
            keywords = words
            break
    
    # 生成歌词
    lyrics = f"""[Verse]
{keywords[0]}在心中燃烧
{keywords[1]}指引我方向
无论风雨多么狂暴
{keywords[2]}就在前方

[Chorus]
让{keywords[0]}带我飞翔
穿越所有阻挡
{keywords[3]}永远闪亮
这是我们的时光

[Verse]
每一个音符都在跳
每一秒都值得骄傲
跟随节奏别停脚
让世界听到我的咆哮

[Chorus]
让{keywords[0]}带我飞翔
穿越所有阻挡
{keywords[3]}永远闪亮
这是我们的时光"""
    
    return lyrics

# 初始化数据库
init_db()  # 允许跨域请求

# 百度千帆 API 配置
QIANFAN_API_KEY = os.getenv('QIANFAN_API_KEY')
QIANFAN_SECRET_KEY = os.getenv('QIANFAN_SECRET_KEY')
QIANFAN_ACCESS_TOKEN = None

# 天谱乐 API 配置
TEMPOLOR_API_KEY = os.getenv('TEMPOLOR_API_KEY')
TEMPOLOR_BASE_URL = "https://api.tianpuyue.cn/open-apis"

# MiniMax API 配置
MINIMAX_API_KEY = os.getenv('MINIMAX_API_KEY')
MINIMAX_BASE_URL = "https://api.minimaxi.com"

# 通义万相 API 配置
TONGYI_API_KEY = os.getenv('TONGYI_API_KEY')
TONGYI_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

# 获取百度千帆访问令牌
def get_qianfan_token():
    global QIANFAN_ACCESS_TOKEN
    if not QIANFAN_ACCESS_TOKEN:
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": QIANFAN_API_KEY,
            "client_secret": QIANFAN_SECRET_KEY
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            QIANFAN_ACCESS_TOKEN = response.json().get("access_token")
    return QIANFAN_ACCESS_TOKEN

# 调用百度千帆大模型
def call_qianfan_model(prompt, model="ernie-3.5-8k"):
    token = get_qianfan_token()
    if not token:
        return None
    
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{model}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get("result")
    return None

# 调用天谱乐 API 生成音乐（异步任务）
def call_tempolor_generate(prompt, duration=30, music_type="vocal", lyrics=None):
    """
    调用天谱乐 API 生成音乐（异步任务）
    :param prompt: 音乐描述/提示词
    :param duration: 音乐时长（秒）
    :param music_type: vocal(带人声) 或 instrumental(纯伴奏)
    :param lyrics: 自定义歌词（可选）
    :return: 任务ID列表
    """
    if not TEMPOLOR_API_KEY:
        print("天谱乐 API Key 未配置")
        return None
    
    # 根据音乐类型选择接口
    if music_type == "vocal":
        url = f"{TEMPOLOR_BASE_URL}/v1/song/generate"
    else:
        url = f"{TEMPOLOR_BASE_URL}/v1/music/generate"
    
    headers = {
        "Authorization": TEMPOLOR_API_KEY,  # 直接使用 API Key，不需要 Bearer
        "Content-Type": "application/json"
    }
    
    # 构建请求参数
    data = {
        "prompt": prompt,
        "model": "TemPolor v4.5",
        "callback_url": "https://example.com/callback"  # 需要配置回调地址
    }
    
    # 如果提供了自定义歌词
    if lyrics and music_type == "vocal":
        data["lyrics"] = lyrics
    
    try:
        print(f"调用天谱乐 API: {url}")
        print(f"请求参数: {data}")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == 200000:
                # 返回任务ID列表
                return result.get("data", {}).get("item_ids", [])
            else:
                print(f"天谱乐 API 错误: {result.get('message')}")
                return None
        else:
            print(f"天谱乐 API 请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"调用天谱乐 API 出错: {str(e)}")
        return None

# 查询天谱乐任务状态
def check_tempolor_task_status(item_ids):
    """
    查询天谱乐任务状态
    :param item_ids: 任务ID列表
    :return: 任务状态信息
    """
    if not TEMPOLOR_API_KEY or not item_ids:
        return None
    
    url = f"{TEMPOLOR_BASE_URL}/v1/song/status"
    headers = {
        "Authorization": TEMPOLOR_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "item_ids": item_ids
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == 200000:
                return result.get("data", {})
        return None
    except Exception as e:
        print(f"查询任务状态出错: {str(e)}")
        return None

# 调用天谱乐 API 生成歌词
def call_tempolor_lyrics(theme, style="pop"):
    """
    调用天谱乐 API 生成歌词
    :param theme: 歌词主题
    :param style: 音乐风格
    :return: 生成的歌词
    """
    if not TEMPOLOR_API_KEY:
        return None
    
    url = f"{TEMPOLOR_BASE_URL}/v1/lyrics/generate"
    headers = {
        "Authorization": f"Bearer {TEMPOLOR_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "theme": theme,
        "style": style,
        "language": "zh"  # 中文歌词
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                return result.get("data", {}).get("lyrics", "")
        return None
    except Exception as e:
        print(f"生成歌词出错: {str(e)}")
        return None

# 调用 MiniMax API 生成歌词
def call_minimax_lyrics(prompt, mode="write_full_song"):
    """
    调用 MiniMax API 生成歌词
    :param prompt: 歌曲主题/风格描述
    :param mode: write_full_song(完整歌曲) 或 edit(编辑)
    :return: 包含歌词、歌名、风格标签的字典
    """
    if not MINIMAX_API_KEY:
        print("MiniMax API Key 未配置")
        return None
    
    url = f"{MINIMAX_BASE_URL}/v1/lyrics_generation"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 优化 prompt，明确要求中文歌词
    chinese_prompt = f"创作一首中文歌曲，主题：{prompt}，要求用中文填写歌词，包含主歌和副歌"
    
    data = {
        "mode": mode,
        "prompt": chinese_prompt
    }
    
    try:
        print(f"调用 MiniMax 歌词生成 API...")
        response = requests.post(url, headers=headers, json=data, timeout=60)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            base_resp = result.get("base_resp", {})
            
            if base_resp.get("status_code") == 0:
                return {
                    "song_title": result.get("song_title", "未知歌名"),
                    "style_tags": result.get("style_tags", ""),
                    "lyrics": result.get("lyrics", ""),
                    "source": "minimax"
                }
            else:
                print(f"MiniMax API 错误: {base_resp.get('status_msg')}")
                return None
        else:
            print(f"MiniMax API 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
    except Exception as e:
        print(f"调用 MiniMax API 出错: {str(e)}")
        return None

# 调用通义万相 API 生成图片
def call_tongyi_image_generate(prompt, size="1024*1024"):
    """
    调用通义万相 API 生成图片
    :param prompt: 图片描述/提示词
    :param size: 图片尺寸，如 "1024*1024", "768*768" 等
    :return: 图片 URL
    """
    if not TONGYI_API_KEY:
        print("通义万相 API Key 未配置")
        return None
    
    url = f"{TONGYI_BASE_URL}/services/aigc/text2image/image-synthesis"
    headers = {
        "Authorization": f"Bearer {TONGYI_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable"  # 启用异步模式
    }
    
    data = {
        "model": "wanx-v1",
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "size": size,
            "n": 1  # 生成1张图片
        }
    }
    
    try:
        print(f"调用通义万相图片生成 API...")
        print(f"提示词: {prompt}")
        
        # 提交异步任务
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"提交任务响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            output = result.get("output", {})
            task_id = output.get("task_id")
            
            if task_id:
                print(f"任务提交成功，任务ID: {task_id}")
                # 轮询查询任务结果
                return check_tongyi_task_result(task_id)
            else:
                print("未获取到任务ID")
                return None
        else:
            print(f"通义万相 API 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
    except Exception as e:
        print(f"调用通义万相 API 出错: {str(e)}")
        return None

# 查询通义万相任务结果
def check_tongyi_task_result(task_id, max_retries=15, interval=2):
    """
    轮询查询通义万相图片生成任务结果
    :param task_id: 任务ID
    :param max_retries: 最大重试次数
    :param interval: 轮询间隔（秒）
    :return: 图片 URL
    """
    if not TONGYI_API_KEY or not task_id:
        return None
    
    url = f"{TONGYI_BASE_URL}/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {TONGYI_API_KEY}"
    }
    
    for i in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                output = result.get("output", {})
                task_status = output.get("task_status")
                
                print(f"任务状态查询 [{i+1}/{max_retries}]: {task_status}")
                
                if task_status == "SUCCEEDED":
                    # 任务完成，获取图片URL
                    results = output.get("results", [])
                    if results and len(results) > 0:
                        img_url = results[0].get("url")
                        print(f"图片生成成功: {img_url}")
                        return img_url
                    return None
                elif task_status in ["FAILED", "CANCELLED"]:
                    print(f"任务失败: {output.get('message', '未知错误')}")
                    return None
                
                # 任务进行中，等待后继续查询
                time.sleep(interval)
            else:
                print(f"查询任务状态失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"查询任务状态出错: {str(e)}")
            return None
    
    print("查询任务结果超时")
    return None

# 调用 MiniMax API 生成音乐
def call_minimax_music(prompt, lyrics, is_instrumental=False):
    """
    调用 MiniMax API 生成音乐
    :param prompt: 音乐描述（风格、情绪、场景）
    :param lyrics: 歌词
    :param is_instrumental: 是否纯音乐（无人声）
    :return: 包含音频数据的字典
    """
    if not MINIMAX_API_KEY:
        print("MiniMax API Key 未配置")
        return None
    
    url = f"{MINIMAX_BASE_URL}/v1/music_generation"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 使用免费模型（更便宜，几分钱/几角钱一首）
    model = "music-2.6-free"  # 免费版本，成本低
    
    # 优化 prompt，强制生成中文歌曲
    chinese_prompt = f"中文歌曲，{prompt}，中文演唱，Mandopop风格"
    
    data = {
        "model": model,
        "prompt": chinese_prompt,
        "is_instrumental": is_instrumental,
        "stream": False
    }
    
    # 如果不是纯音乐，添加歌词（确保是中文歌词）
    if not is_instrumental and lyrics:
        # 如果歌词是英文，添加中文提示
        if not any('\u4e00' <= char <= '\u9fff' for char in lyrics[:100]):
            lyrics = f"[Verse]\n这是一首中文歌曲\n用中文演唱\n表达情感\n\n[Chorus]\n中文歌词\n优美动听\n\n{lyrics}"
        data["lyrics"] = lyrics
    
    try:
        print(f"调用 MiniMax 音乐生成 API...")
        print(f"模型: {model}, 纯音乐: {is_instrumental}")
        # 付费模型通常更快，设置90秒超时
        response = requests.post(url, headers=headers, json=data, timeout=90)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            base_resp = result.get("base_resp", {})
            
            if base_resp.get("status_code") == 0:
                data_info = result.get("data", {})
                extra_info = result.get("extra_info", {})
                
                # 获取音频数据
                audio_data = data_info.get("audio", "")
                audio_url = None
                
                if audio_data:
                    if audio_data.startswith("http"):
                        # 直接是URL
                        audio_url = audio_data
                    else:
                        # 是hex编码的音频数据，保存为本地文件并提供URL
                        import hashlib
                        audio_filename = f"music_{hashlib.md5(prompt.encode()).hexdigest()[:8]}_{int(time.time())}.mp3"
                        audio_path = os.path.join(os.path.dirname(__file__), 'static', audio_filename)
                        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                        with open(audio_path, 'wb') as f:
                            f.write(bytes.fromhex(audio_data))
                        audio_url = f"http://localhost:5000/static/{audio_filename}"
                        print(f"音频保存为本地文件: {audio_url}")
                
                if not audio_url:
                    print("未能获取音频URL")
                    return None
                
                return {
                    "audio_url": audio_url,
                    "status": data_info.get("status", 0),
                    "duration": extra_info.get("music_duration", 0) / 1000 if extra_info.get("music_duration") else 0,
                    "source": "minimax"
                }
            else:
                print(f"MiniMax API 错误: {base_resp.get('status_msg')}")
                return None
        else:
            print(f"MiniMax API 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
    except Exception as e:
        print(f"调用 MiniMax API 出错: {str(e)}")
        return None

# 风格分析接口
@app.route('/api/v1/style-analysis', methods=['POST'])
def style_analysis():
    try:
        data = request.json
        theme = data.get('theme')
        if not theme:
            return jsonify({"code": 400, "message": "缺少分析主题", "data": None})
        
        # 构建分析提示词
        analysis_prompt = f"请分析{theme}的音乐特征，按照以下结构输出：\n" \
                         "🎵 旋律特征：\n" \
                         "采用XX音阶，节奏XX，旋律走向XX，带有XX风格的典型旋律动机\n" \
                         "\n" \
                         "🎸 编曲特征：\n" \
                         "核心乐器：XX、XX、XX\n" \
                         "配器层次：XX为主，XX点缀，XX铺底\n" \
                         "制作风格：XX混音，XX声场\n" \
                         "\n" \
                         "💖 情感基调：\n" \
                         "整体情绪：XX，适合XX场景\n" \
                         "情绪层次：从XX到XX，带有XX的氛围感"
        
        result = call_qianfan_model(analysis_prompt)
        if result:
            return jsonify({"code": 200, "message": "success", "data": {"result": result}})
        else:
            return jsonify({"code": 500, "message": "分析失败", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

# 专业 Prompt 生成接口
@app.route('/api/v1/generate-prompt', methods=['POST'])
def generate_prompt():
    try:
        data = request.json
        role = data.get('role')
        style_analysis = data.get('style_analysis')
        task = data.get('task')
        
        if not role or not style_analysis or not task:
            return jsonify({"code": 400, "message": "缺少必要参数", "data": None})
        
        # 构建生成提示词
        prompt = f"{role}\n\n{style_analysis}\n\n{task}"
        result = call_qianfan_model(prompt)
        
        if result:
            return jsonify({"code": 200, "message": "success", "data": {"prompt": result}})
        else:
            return jsonify({"code": 500, "message": "生成失败", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

# 音乐生成接口（支持天谱乐 AI）
@app.route('/api/v1/generate-music', methods=['POST'])
def generate_music():
    try:
        data = request.json
        prompt = data.get('prompt')
        duration = int(data.get('duration', 30))
        music_type = data.get('music_type', 'vocal')  # vocal 或 instrumental
        music_lang = data.get('lang', '中文')  # 语言：中文/粤语/英文
        music_style = data.get('style', '流行')  # 风格：流行/摇滚/电子等
        custom_lyrics = data.get('lyrics', None)  # 自定义歌词（可选）
        
        if not prompt:
            return jsonify({"code": 400, "message": "缺少音乐描述", "data": None})
        
        # 优先尝试调用 MiniMax API 生成音乐（使用免费模型，成本低）
        is_instrumental = music_type == "instrumental"
        
        music_list = []
        
        # 根据用户输入的主题选择封面关键词
        theme_keywords = {
            '爱': 'love romantic',
            '情': 'love heart',
            '梦': 'dream sky stars',
            '夜': 'night city lights',
            '雨': 'rain mood',
            '海': 'ocean beach waves',
            '山': 'mountain nature',
            '花': 'flower bloom',
            '雪': 'snow winter',
            '风': 'wind freedom',
            '火': 'fire passion',
            '光': 'light shine',
            '星': 'starry galaxy',
            '月': 'moon night',
            '春': 'spring blossom',
            '夏': 'summer beach',
            '秋': 'autumn leaves',
            '冬': 'winter snow',
            '朋友': 'friendship together',
            '家': 'home warm',
            '路': 'road journey',
            '时间': 'time clock',
            '记忆': 'memory vintage',
            '希望': 'hope sunrise',
            '自由': 'freedom fly',
            '和平': 'peace dove',
            '力量': 'power strength',
            '美丽': 'beauty art',
            '快乐': 'happy joy',
            '悲伤': 'sad melancholy',
            '孤独': 'lonely alone',
            '思念': 'missing longing',
            '等待': 'waiting patience',
            '告别': 'goodbye farewell',
            '重逢': 'reunion meet',
            '青春': 'youth young',
            '童年': 'childhood memory',
            '未来': 'future technology',
            '过去': 'past vintage',
            '现在': 'present moment'
        }
        
        # 找到匹配的关键词
        matched_keyword = 'music'
        for key, keyword in theme_keywords.items():
            if key in prompt:
                matched_keyword = keyword
                break
        
        # 只生成一首歌曲，使用用户选择的语言和风格
        style_prompt = f"{prompt}，{music_lang}歌曲，{music_style}风格"
        
        # 确定歌词（优先级：自定义歌词 > MiniMax生成 > 本地模板）
        if not is_instrumental:
            if custom_lyrics:
                style_lyrics = custom_lyrics
                print("使用用户自定义歌词")
            else:
                print("调用 MiniMax 生成歌词...")
                lyrics_result = call_minimax_lyrics(style_prompt)
                if lyrics_result and lyrics_result.get("lyrics"):
                    style_lyrics = lyrics_result["lyrics"]
                    print("MiniMax 歌词生成成功")
                else:
                    style_lyrics = generate_fast_lyrics(style_prompt)
                    print("使用本地模板歌词")
        else:
            style_lyrics = None
        
        # 生成音乐
        music_result = call_minimax_music(style_prompt, style_lyrics, is_instrumental)
        
        if music_result and music_result.get("audio_url"):
            # 使用通义万相生成与主题相关的封面
            cover_prompt = f"音乐专辑封面，{prompt}，{music_style}风格，艺术插画，高品质，无文字"
            cover_url = call_tongyi_image_generate(cover_prompt, "1024*1024")
            
            # 如果通义万相失败，使用Unsplash作为回退
            if not cover_url:
                random_id = int(time.time())
                cover_url = f"https://source.unsplash.com/400x400/?{matched_keyword}&sig={random_id}"
            
            music_data = {
                "audio_url": music_result["audio_url"],
                "duration": duration,
                "title": f"{music_lang}{music_style} - {prompt[:20]}...",
                "lyrics": style_lyrics or "[纯音乐 - 无歌词]",
                "cover_url": cover_url,
                "music_type": music_type,
                "source": "minimax",
                "model": "music-2.6-free"
            }
            music_list.append(music_data)
        
        # 如果成功生成至少一首，返回结果
        if len(music_list) > 0:
            return jsonify({
                "code": 200, 
                "message": "success", 
                "data": music_list
            })
        
        # 如果 MiniMax API 调用失败，回退到免费音乐示例
        print("MiniMax API 调用失败，使用免费AI音乐示例")
        
        # 使用真正带人声的免费音乐示例
        # 注意：这些音乐的实际时长可能与用户选择的不同，前端会处理播放时长
        if music_type == 'vocal':
            music_list = [
                {
                    "audio_url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=pop-dance-113774.mp3",
                    "duration": duration,
                    "actual_duration": 180,
                    "title": f"流行舞曲 - {prompt[:10]}...",
                    "lyrics": "🎵 主歌：\n在星光下起舞，心跳跟着节奏\n梦想在前方，我们不再停留\n每一个音符，都是新的追求\n让音乐带领我们，飞向那自由\n\n🎤 副歌：\n跟着节拍摇摆，让烦恼都走开\n这一刻只属于你和我\n音乐响起时，世界都变美好\n让我们一起唱这首歌",
                    "cover_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=400&fit=crop",
                    "music_type": music_type,
                    "source": "free-vocal"
                }
            ]
        else:
            music_list = [
                {
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                    "duration": duration,
                    "title": f"纯音乐 - {prompt[:10]}...",
                    "lyrics": "[纯音乐 - 无歌词]\n这是一首优美的伴奏曲，适合背景音乐使用。\n钢琴和合成器的完美结合，营造出宁静的氛围。",
                    "cover_url": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop",
                    "music_type": music_type,
                    "source": "mock"
                }
            ]
        
        # 自动保存生成的音乐到数据库
        for music in music_list:
            music_record = {
                'title': music['title'],
                'prompt': prompt,
                'lyrics': music.get('lyrics', ''),
                'audio_url': music['audio_url'],
                'cover_url': music.get('cover_url', ''),
                'duration': music['duration'],
                'music_type': music['music_type'],
                'source': music['source']
            }
            save_music_record(music_record)
            print(f"已保存音乐记录: {music['title']}")
        
        return jsonify({"code": 200, "message": "success", "data": music_list})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

# 图片生成接口
@app.route('/api/v1/generate-image', methods=['POST'])
def generate_image():
    """生成音乐封面图片 - 使用Unsplash快速获取"""
    try:
        data = request.json
        prompt = data.get('prompt', 'music')
        
        # 将中文主题映射到英文关键词（用于Unsplash搜索）
        keyword_map = {
            '校园': 'campus school youth',
            '青春': 'youth young energy',
            '爱情': 'love romantic',
            '梦想': 'dream sky star',
            '夜晚': 'night city lights',
            '自然': 'nature landscape',
            '海洋': 'ocean sea wave',
            '森林': 'forest tree green',
            '城市': 'city urban building',
            '星空': 'starry sky galaxy',
            '日落': 'sunset orange sky',
            '花朵': 'flower bloom colorful',
            '音乐': 'music concert instrument',
            '派对': 'party celebration',
            '旅行': 'travel adventure road',
            '咖啡': 'coffee cafe warm',
            '书籍': 'book reading library',
            '雨': 'rain wet window',
            '雪': 'snow winter white',
            '春天': 'spring flower blossom',
            '夏天': 'summer beach sun',
            '秋天': 'autumn fall leaves',
            '冬天': 'winter snow cold'
        }
        
        # 查找匹配的关键词
        search_keyword = 'music abstract'
        for cn, en in keyword_map.items():
            if cn in prompt:
                search_keyword = en
                break
        
        # 使用 Unsplash Source API 快速获取图片（无需等待生成）
        # 添加随机参数避免缓存
        random_id = int(time.time()) % 1000
        image_url = f"https://source.unsplash.com/400x400/?{urllib.parse.quote(search_keyword)}&sig={random_id}"
        
        return jsonify({
            "code": 200, 
            "message": "success", 
            "data": {
                "image_url": image_url,
                "source": "unsplash",
                "keyword": search_keyword
            }
        })
    except Exception as e:
        # 出错时返回默认渐变图片
        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "image_url": "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=400&h=400&fit=crop",
                "source": "default"
            }
        })

# 保存音乐记录接口
@app.route('/api/v1/save-music', methods=['POST'])
def save_music():
    """保存生成的音乐到历史记录"""
    try:
        data = request.json
        
        # 验证必要字段
        if not data.get('title') or not data.get('audio_url'):
            return jsonify({"code": 400, "message": "缺少必要字段", "data": None})
        
        # 保存到数据库
        record_id = save_music_record(data)
        
        if record_id:
            return jsonify({
                "code": 200, 
                "message": "保存成功", 
                "data": {"id": record_id}
            })
        else:
            return jsonify({"code": 500, "message": "保存失败", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

# 获取音乐历史记录接口
@app.route('/api/v1/music-history', methods=['GET'])
def get_history():
    """获取音乐生成历史"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = get_music_history(limit)
        
        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "total": len(history),
                "records": history
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

# 删除音乐记录接口
@app.route('/api/v1/delete-music/<int:record_id>', methods=['DELETE'])
def delete_music(record_id):
    """删除音乐记录"""
    try:
        success = delete_music_record(record_id)
        
        if success:
            return jsonify({"code": 200, "message": "删除成功", "data": None})
        else:
            return jsonify({"code": 500, "message": "删除失败", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

# 查询天谱乐任务状态接口
@app.route('/api/v1/check-task', methods=['POST'])
def check_task():
    """查询天谱乐音乐生成任务状态"""
    try:
        data = request.json
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return jsonify({"code": 400, "message": "缺少任务ID", "data": None})
        
        # 查询任务状态
        task_status = check_tempolor_task_status(task_ids)
        
        if task_status:
            return jsonify({"code": 200, "message": "success", "data": task_status})
        else:
            return jsonify({"code": 500, "message": "查询任务状态失败", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

# 歌词生成接口
@app.route('/api/v1/generate-lyrics', methods=['POST'])
def generate_lyrics():
    """生成歌词接口"""
    try:
        data = request.json
        theme = data.get('theme')
        style = data.get('style', 'pop')
        
        if not theme:
            return jsonify({"code": 400, "message": "缺少主题", "data": None})
        
        # 优先使用 MiniMax API 生成歌词（质量更好，支持结构标签）
        minimax_result = call_minimax_lyrics(theme)
        
        if minimax_result:
            return jsonify({
                "code": 200, 
                "message": "success", 
                "data": {
                    "lyrics": minimax_result["lyrics"],
                    "song_title": minimax_result["song_title"],
                    "style_tags": minimax_result["style_tags"],
                    "source": "minimax"
                }
            })
        
        # 回退到百度千帆生成歌词
        prompt = f"请为'{theme}'这个主题创作一首{style}风格的中文歌词。要求：\n1. 包含主歌和副歌\n2. 语言优美，有诗意\n3. 适合演唱\n4. 长度适中，约200-300字"
        
        result = call_qianfan_model(prompt)
        if result:
            return jsonify({"code": 200, "message": "success", "data": {"lyrics": result, "source": "qianfan"}})
        else:
            return jsonify({"code": 500, "message": "歌词生成失败", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e), "data": None})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
# 🎵 AI 音乐生成器

基于 MiniMax 音乐生成 API 的智能音乐创作工具，支持多语言、多风格歌曲生成，含专辑封面自动生成与歌词滚动播放。

## ✨ 功能特性

- 🎤 **AI 歌曲生成**：调用 MiniMax music-2.6-free 生成带人声演唱的原创歌曲
- 🌏 **多语言支持**：中文、粤语、英文
- 🎸 **多风格选择**：流行、摇滚、电子、民谣、R&B、说唱、爵士、古典、国风
- 🖼️ **智能封面**：通义万相 AI 自动生成与音乐主题相关的专辑封面
- 📜 **歌词滚动**：播放时歌词高亮同步滚动
- 📚 **历史记录**：SQLite 持久化保存所有生成记录
- ⏱️ **时长选择**：30秒 / 1分钟 / 2分钟 / 3分钟

## 📁 项目结构

```
ai-music-generator/
├── frontend/
│   ├── index.html      # 页面结构
│   ├── style.css       # 样式文件
│   ├── app.js          # 交互逻辑
│   └── netlify.toml    # Netlify 部署配置
├── backend/
│   ├── app.py          # Flask 后端服务
│   ├── requirements.txt
│   ├── render.yaml     # Render 部署配置
│   └── .env            # 环境变量（不上传）
└── README.md
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML + Tailwind CSS + 原生 JavaScript |
| 后端 | Python + Flask + Flask-CORS |
| 音乐生成 | MiniMax music-2.6-free API |
| 封面生成 | 通义万相 wanx-v1 API |
| 歌词生成 | MiniMax 歌词 API + 本地模板兜底 |
| 数据库 | SQLite |
| 部署 | 前端 Netlify + 后端 Render |

## 🚀 本地运行

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `backend/.env` 文件：

```env
MINIMAX_API_KEY=你的MiniMax API Key
TONGYI_API_KEY=你的通义万相 API Key
QIANFAN_API_KEY=你的百度千帆 API Key
```

### 3. 启动后端

```bash
cd backend
python app.py
```

后端运行在 `http://localhost:5000`

### 4. 打开前端

直接用浏览器打开 `frontend/index.html`，或：

```bash
cd frontend
python -m http.server 8080
```

访问 `http://localhost:8080`

## ☁️ 线上部署

### 后端 → Render

1. 登录 [render.com](https://render.com)，新建 Web Service
2. 连接 GitHub 仓库，Root Directory 设为 `ai-music-generator/backend`
3. Build Command：`pip install -r requirements.txt`
4. Start Command：`gunicorn app:app --bind 0.0.0.0:$PORT`
5. 在 Environment Variables 添加三个 API Key

### 前端 → Netlify

1. 登录 [netlify.com](https://netlify.com)
2. 新建站点，连接 GitHub 仓库
3. Base directory：`ai-music-generator/frontend`
4. Publish directory：`ai-music-generator/frontend`
5. 部署完成后，在 `app.js` 第 4 行将后端地址替换为 Render 服务地址

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generate-music` | POST | 生成音乐 |
| `/api/v1/generate-lyrics` | POST | 生成歌词 |
| `/api/v1/music-history` | GET | 获取历史记录 |
| `/api/v1/delete-music/<id>` | DELETE | 删除记录 |

## 📝 生成音乐请求示例

```json
{
  "prompt": "一首关于夏天海边的流行歌曲",
  "duration": 60,
  "music_type": "vocal",
  "lang": "中文",
  "style": "流行",
  "lyrics": "可选的自定义歌词"
}
```

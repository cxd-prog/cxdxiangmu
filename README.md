# AI 音乐生成全流程演示系统

## 项目介绍

这是一个通用 AI 音乐生成演示工具，支持任意风格/主题，界面现代高颜值，功能丝滑闭环，完美适配三次实时录屏演示。

## 项目结构

```
ai-music-generator/
├── frontend/            # 前端代码
│   └── index.html       # 主页面
├── backend/             # 后端代码
│   ├── app.py           # Flask 应用
│   ├── requirements.txt # 依赖文件
│   └── .env             # 环境变量配置
└── README.md            # 部署说明
```

## 技术栈

- 前端：HTML + CSS + JavaScript + Tailwind CSS
- 后端：Python + Flask + 百度千帆 API

## 核心功能

1. **直接生成**：输入任意 Prompt，直接生成音乐
2. **风格分析**：分析任意主题/风格，提取专业音乐特征
3. **Agent 编排**：角色 + 分析 + 指令，生成专业级音乐 Prompt

## 部署步骤

### 1. 安装依赖

#### 后端依赖

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `backend/.env` 文件，填写百度千帆 API Key 和 Secret Key：

```env
# 百度千帆 API 配置
QIANFAN_API_KEY=your_api_key_here
QIANFAN_SECRET_KEY=your_secret_key_here
```

### 3. 启动服务

#### 启动后端服务

```bash
# 进入后端目录
cd backend

# 启动 Flask 服务
python app.py
```

后端服务将在 `http://localhost:5000` 运行。

#### 启动前端服务

可以使用任何静态文件服务器来托管前端文件，例如：

```bash
# 进入前端目录
cd frontend

# 使用 Python 内置服务器
python -m http.server 8000
```

前端页面将在 `http://localhost:8000` 访问。

## 接口说明

### 1. 风格分析接口

- 地址：`/api/v1/style-analysis`
- 方法：POST
- 请求参数：
  ```json
  {
    "theme": "用户输入的分析主题"
  }
  ```
- 响应参数：
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "result": "结构化的风格分析结果"
    }
  }
  ```

### 2. 专业 Prompt 生成接口

- 地址：`/api/v1/generate-prompt`
- 方法：POST
- 请求参数：
  ```json
  {
    "role": "角色设定内容",
    "style_analysis": "风格分析结果",
    "task": "任务指令"
  }
  ```
- 响应参数：
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "prompt": "生成的专业音乐Prompt"
    }
  }
  ```

### 3. 音乐生成接口

- 地址：`/api/v1/generate-music`
- 方法：POST
- 请求参数：
  ```json
  {
    "prompt": "音乐生成Prompt"
  }
  ```
- 响应参数：
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "audio_url": "音频播放链接",
      "duration": 30, // 音频时长，单位秒
      "title": "生成的音乐标题"
    }
  }
  ```

## 录屏演示建议

1. **第一次录制**：使用「直接生成」标签页，输入简单 Prompt 生成音乐
2. **第二次录制**：使用「风格分析」标签页，输入分析主题，获取专业音乐特征
3. **第三次录制**：使用「Agent 编排」标签页，粘贴风格分析结果，生成专业 Prompt，然后一键跳转生成音乐

建议使用 1920×1080 分辨率，浏览器全屏显示，确保录屏效果最佳。

## 注意事项

1. 请确保已正确配置百度千帆 API Key 和 Secret Key
2. 音乐生成接口当前为模拟实现，需要对接实际的音乐生成 API 才能生成真实的音乐
3. 演示前请提前测试所有接口，确保响应时间 < 5 秒
4. 静态资源已进行压缩，保证页面加载速度 < 1 秒
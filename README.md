# EasyCode - AI 编程助手平台

基于 Kimi API 的智能编程助手，提供代码生成、项目规划、代码修复、语音交互等功能。

## 项目简介

**EasyCode** 是一个全栈 AI 编程辅助工具，包含：

- **前端**: Vue 3 + TypeScript + Vite，使用 Element Plus 组件库和 TailwindCSS 样式，集成 Vue Flow 实现可视化节点编排
- **后端**: FastAPI + Python，集成 Kimi 大模型 API、语音识别(sherpa-onnx)、代码沙盒执行、SQLite 数据存储

### 主要功能

| 模块 | 功能描述 |
|------|----------|
| 🤖 AI 对话 | 基于 Kimi API 的智能代码生成与问答 |
| 📋 项目规划 | AI 辅助项目架构设计与任务拆解 |
| 🔧 代码修复 | 自动分析代码错误并提供修复建议 |
| 🎙️ 语音交互 | 语音输入与 AI 语音回复 |
| 📁 项目管理 | 项目创建、文件管理、会话历史 |
| 🏖️ 沙盒执行 | 安全的代码运行环境 |

---

## 安装指南

### 环境要求

- Python 3.10+
- Node.js 18+

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd EasyCode
```

### 2. 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 前端安装

```bash
cd ../frontend

# 安装依赖
npm install
```

---

## 配置环境变量

在 `backend/.env` 文件中配置 API 密钥：

```env
# backend/.env
KIMI_API_KEY=your-kimi-api-key-here
KIMI_BASE_URL=https://api.kimi.com/coding/
```

> ⚠️ **重要**: 
> - 需要将 `your-kimi-api-key-here` 替换为你自己的 [Kimi API Key](https://platform.moonshot.cn/)
> - `.env` 文件格式为 `KEY=value`，**不要加引号**，**不要有空格**

---

## 启动服务

### 方式一：分别启动（推荐开发使用）

**终端 1 - 启动后端：**
```bash
cd backend
venv\Scripts\activate  # Windows 激活虚拟环境
python main.py
```
后端服务将运行在 `http://localhost:8000`

**终端 2 - 启动前端：**
```bash
cd frontend
npm run dev
```
前端开发服务器将运行在 `http://localhost:5173`

### 方式二：后台服务（生产部署）

使用 uvicorn 以生产模式运行后端：
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 项目结构

```
EasyCode/
├── backend/              # 后端服务
│   ├── core/            # 核心配置
│   │   └── config.py    # 环境变量配置（读取 .env）
│   ├── routers/         # API 路由
│   ├── services/        # 业务逻辑
│   ├── main.py          # 应用入口
│   ├── requirements.txt # Python 依赖
│   └── .env             # ⚠️ 环境变量配置文件
│
└── frontend/            # 前端应用
    ├── src/             # 源代码
    ├── package.json     # Node 依赖
    └── vite.config.ts   # Vite 配置
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + TypeScript + Vite |
| UI 组件 | Element Plus + TailwindCSS |
| 可视化 | Vue Flow |
| 代码编辑 | Monaco Editor |
| 后端框架 | FastAPI |
| AI 模型 | Kimi API |
| 语音识别 | sherpa-onnx |
| 数据库 | SQLite |

---

## 许可证

MIT License

# [项目名称] - 本地 RAG 聊天机器人

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

中文｜<a href="https://github.com/Talen-520/StockAgent/blob/main/README.md">English</a>

这是一个功能齐全的本地 RAG (Retrieval-Augmented Generation) 聊天应用。它使用 [Ollama](https://ollama.com/) 在本地运行开源大语言模型 (如 Gemma)，并借助 [Qdrant](https://qdrant.tech/) 向量数据库进行高效的语义搜索，最终通过一个现代化的 Web UI 提供交互式聊天体验。

整个应用完全在你的本地机器上运行，确保了数据的隐私和安全。

---

## 🏛️ 技术架构

本项目由四个核心组件构成：

1.  **🧠 本地大语言模型 (LLM)**: 使用 **Ollama** 部署和管理本地的开源模型 (例如 Google 的 `gemma`)。
2.  **📦 向量数据库 (Vector DB)**: 使用 **Qdrant** 存储文本的向量嵌入，并通过 Docker 运行。
3.  **⚙️ 后端服务 (Backend)**: 使用 **Python** 编写，负责处理业务逻辑，连接 Ollama 和 Qdrant。使用 `uv`进行包管理。
4.  **🎨 前端界面 (Frontend)**: 一个位于 `qdrant-web/` 目录下的 **Node.js** Web 应用，为用户提供聊天界面。

## 📋 先决条件

在开始之前，请确保你的系统上已安装以下所有工具：

* **Git**: 用于克隆代码仓库。
* **Python 3.13+**: [官方下载地址](https://www.python.org/downloads/)。
* **[uv](https://github.com/astral-sh/uv)**: 一个极速的 Python 包安装和解析器。
    ```bash
    # macOS / Linux
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    # Windows
    powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
    ```
* **Node.js**: v18 或更高版本。 [官方下载地址](https://nodejs.org/)。
* **Docker**: 用于运行 Qdrant 向量数据库。 [官方下载地址](https://www.docker.com/products/docker-desktop/)。
* **[Ollama](https://ollama.com/)**: 用于在本地运行大语言模型。请访问官网下载并安装。

## 🚀 部署与运行指南

请按照以下步骤，一步步设置并启动整个应用。

### 第一步：克隆仓库并安装模型

1.  **克隆本代码仓库**
    ```bash
    git clone https://github.com/Talen-520/Qdrant-Local-RAG.git
    cd Qdrant-Local-RAG
    ```

2.  **下载并运行 Ollama 模型**
    安装 Ollama 后，在终端执行以下命令来下载并首次运行 `gemma` 模型。这可能需要一些时间，取决于你的网络和硬件。

    ```bash
    ollama run gemma
    ```
    > 你可以替换成任何你想使用的其他 Ollama 模型，例如 `llama3`, `mistral` 等。

### 第二步：启动 Qdrant 向量数据库

我们将使用 Docker 来运行 Qdrant 服务，这样可以确保环境隔离且干净。

1.  **拉取 Qdrant 镜像**
    ```bash
    docker pull qdrant/qdrant
    ```

2.  **创建并运行容器**
    此命令会创建一个名为 `local-qdrant-container` 的容器，并将数据持久化存储在项目目录下的 `qdrant_storage` 文件夹中。

    ```bash
    # 对于 macOS / Linux
    docker run -d --name local-qdrant-container -p 6333:6333 -p 6334:6334 -v "$(pwd)/qdrant_storage:/qdrant/storage" qdrant/qdrant

    # 对于 Windows (PowerShell)
    docker run -d --name local-qdrant-container -p 6333:6333 -p 6334:6334 -v "${PWD}/qdrant_storage:/qdrant/storage" qdrant/qdrant
    ```

### 第三步：安装项目依赖

1.  **安装 Python 后端依赖**
    在项目根目录运行 `uv sync`，它会自动创建虚拟环境并安装 `pyproject.toml` 中定义的所有依赖。
    ```bash
    uv sync
    ```

2.  **安装 Node.js 前端依赖**
    ```bash
    cd qdrant-web
    npm install
    cd .. 
    ```

### 第四步：启动所有服务

现在所有组件都已准备就绪，可以启动应用了！**建议打开三个独立的终端窗口**来分别运行各项服务。

1.  **终端 1: 确保 Qdrant 正在运行**
    如果之前容器已停止，使用以下命令启动它。
    ```bash
    docker start local-qdrant-container
    ```
    > 你可以使用 `docker ps` 命令来检查容器是否正在运行。

2.  **终端 2: 启动后端服务**
    在项目 **根目录** 下运行：
    ```bash
    uv run backend/server.py
    ```

3.  **终端 3: 启动前端 Web UI**
    在项目 **根目录** 下运行：
    ```bash
    cd qdrant-web
    npm run dev
    ```

### 第五步：开始聊天！

所有服务启动成功后，打开你的浏览器并访问以下地址：

➡️ **http://localhost:5173/**

现在你可以开始与你的本地 RAG 聊天机器人进行对话了！

## ⚙️ 日常管理

#### 停止 Qdrant 容器
当你不需要使用时，可以停止数据库容器以释放资源。
```bash
docker stop local-qdrant-container
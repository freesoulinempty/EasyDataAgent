# EasyDataAgent 🤖📊

**专业级数据分析AI助手** | **Professional Data Analysis AI Assistant**

一个基于LangGraph和OpenAI的智能数据分析代理，支持自然语言交互进行数据分析、可视化、机器学习和数据库查询。完全本地部署，数据安全可控。

*An intelligent data analysis agent built with LangGraph and OpenAI, supporting natural language interactions for data analysis, visualization, machine learning, and database queries. Fully local deployment with secure data handling.*

## 🌟 核心特性 | Key Features

### 📊 **数据分析能力**
- **数据预览快照** - 快速了解数据结构和质量
- **数据质量检查** - 深度分析缺失值、异常值、重复值
- **SQL查询与数据提取** - 连接数据库，执行复杂查询
- **Python数据处理** - 统计分析、数据清洗、特征工程

### 📈 **可视化功能**
- **智能图表生成** - 散点图、柱状图、热力图、箱线图等
- **动态图片命名** - 每个图表使用描述性文件名，避免覆盖
- **自定义可视化** - 根据数据特征自动选择最佳图表类型
- **图片自动显示** - 生成的图表自动在前端界面展示

### 🤖 **机器学习**
- **分类与回归** - 自动模型选择和训练
- **聚类分析** - 无监督学习和模式识别
- **特征工程** - 自动特征生成和选择
- **模型评估** - 全面的性能指标和可视化

### 💾 **数据导出**
- **多格式导出** - Excel、JSON、PDF格式
- **查询历史管理** - 保存和重用常用SQL查询
- **报告生成** - 自动生成分析报告

### 🔍 **智能搜索**
- **Web搜索集成** - Tavily搜索获取实时信息
- **上下文理解** - 基于数据内容提供相关建议

## 🏗️ 技术架构 | Architecture

### **后端 Backend**
- **LangGraph** - AI代理框架和工作流编排
- **LangChain** - 工具链和模型集成
- **OpenAI GPT-4** - 核心语言模型
- **Python生态** - pandas, matplotlib, seaborn, scikit-learn
- **数据库支持** - MySQL, PostgreSQL, Redis

### **前端 Frontend**
- **Next.js** - React框架和服务端渲染
- **Agent Chat UI** - 专业的AI对话界面
- **实时通信** - WebSocket连接支持
- **图片展示** - 自动渲染生成的图表

### **基础设施 Infrastructure**
- **Docker容器化** - 完整的容器化部署
- **Docker Compose** - 多服务编排
- **共享存储** - 前后端数据共享
- **健康检查** - 服务状态监控

## 🚀 快速开始 | Quick Start

### 📋 环境要求 | Prerequisites

- **Docker** 20.10+ 和 **Docker Compose** 2.0+
- **Git** 用于克隆仓库
- **OpenAI API Key** (必需)
- **Tavily API Key** (可选，用于网络搜索)
- **LangSmith API Key** (可选，用于追踪)

### 🎯 Option 1: 一键部署 (推荐) | One-Click Deployment (Recommended)

#### **开发/测试环境 (包含所有数据库)**

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/EasyDataAgent.git
cd EasyDataAgent

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，添加你的 API Keys

# 3. 一键启动 (包含 MySQL, PostgreSQL, Redis)
docker-compose up -d

# 4. 等待服务启动 (约1-2分钟)
docker-compose ps

# 5. 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8123
```

#### **生产环境 (使用您的数据库)**

```bash
# 1. 下载生产配置
wget https://raw.githubusercontent.com/your-username/EasyDataAgent/main/docker-compose.prod.yml

# 2. 配置环境变量
cat > .env << EOF
# === 必需的API Keys ===
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here

# === 数据库连接 (LangGraph需要) ===
REDIS_URI=redis://your-redis-host:6379
DATABASE_URI=postgres://user:password@your-postgres-host:5432/langgraph

# === 您的业务数据库 (MySQL) ===
HOST=your-mysql-host
USER=your-mysql-user
MYSQL_PW=your-mysql-password
DB_NAME=your-database-name
PORT=3306

# === 可选配置 ===
MODEL_NAME=gpt-4-mini
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=easy_data_agent
EOF

# 3. 启动应用 (仅应用容器，使用您的数据库)
docker-compose -f docker-compose.prod.yml up -d

# 4. 检查状态
docker-compose -f docker-compose.prod.yml ps
```

### 🔧 Option 2: 本地开发部署 | Local Development

#### **后端开发环境设置**

```bash
# 1. 进入后端目录
cd backend

# 2. 安装 UV (现代Python包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或者使用 pip: pip install uv

# 3. 创建虚拟环境并安装依赖
uv venv --python 3.11
source .venv/bin/activate  # Linux/Mac
# 或者: .venv\Scripts\activate  # Windows

uv pip install -r requirements.txt

# 4. 安装 LangGraph CLI
uv add langgraph-cli

# 5. 配置环境变量
cat > .env << EOF
# 数据库连接
HOST=localhost
USER=your-mysql-user
MYSQL_PW=your-mysql-password
DB_NAME=your-database-name
PORT=3306

# API Keys
OPENAI_API_KEY=your-openai-key
TAVILY_API_KEY=your-tavily-key
LANGSMITH_API_KEY=your-langsmith-key

# LangGraph配置
REDIS_URI=redis://localhost:6379
DATABASE_URI=postgres://postgres:postgres@localhost:5432/langgraph

# 路径配置
PUBLIC_DIR=../frontend/public
PROJECT_ROOT=.
EOF

# 6. 构建后端镜像 (可选)
uv run langgraph build --tag easydataagent-backend:latest

# 7. 启动开发服务器
uv run langgraph dev
# 后端将在 http://localhost:8123 启动
```

#### **前端开发环境设置**

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖 (使用 pnpm)
npm install -g pnpm
pnpm install

# 3. 配置环境变量
echo "NEXT_PUBLIC_API_URL=http://localhost:8123" > .env.local

# 4. 启动开发服务器
pnpm dev
# 前端将在 http://localhost:3000 启动
```

## 📁 项目结构 | Project Structure

```
EasyDataAgent/
├── backend/                    # 后端服务 (Python + LangGraph)
│   ├── graph.py               # 主要的AI代理逻辑
│   ├── prompt.txt             # AI代理的系统提示词
│   ├── langgraph.json         # LangGraph配置文件
│   ├── requirements.txt       # Python依赖
│   └── .env.example          # 环境变量示例
├── frontend/                   # 前端服务 (Next.js)
│   ├── src/                   # 源代码
│   ├── public/               # 静态文件
│   ├── package.json          # Node.js依赖
│   └── Dockerfile            # 前端Docker配置
├── docker-compose.yml         # 开发环境编排 (包含数据库)
├── docker-compose.prod.yml    # 生产环境编排 (仅应用)
├── .env.example              # 环境变量模板
└── README.md                 # 项目文档
```

## 🛠️ 高级配置 | Advanced Configuration

### **自定义后端镜像构建**

```bash
# 进入后端目录
cd backend

# 激活虚拟环境
source .venv/bin/activate

# 使用 LangGraph CLI 构建
uv run langgraph build --tag my-custom-agent:latest

# 推送到Docker Hub (可选)
docker tag my-custom-agent:latest yourusername/my-agent:latest
docker push yourusername/my-agent:latest

# 更新 docker-compose.yml 使用自定义镜像
# 将 "image: gugu689/data_agent:latest" 
# 改为 "image: yourusername/my-agent:latest"
```

### **环境变量详解**

```env
# === 核心AI服务 ===
OPENAI_API_KEY=sk-...                    # OpenAI API密钥 (必需)
MODEL_NAME=gpt-4-mini                    # 使用的模型 (可选)

# === 网络搜索 ===
TAVILY_API_KEY=tvly-...                  # Tavily搜索API (可选)

# === LangSmith追踪 ===
LANGSMITH_API_KEY=ls_...                 # LangSmith API (可选)
LANGSMITH_TRACING=true                   # 启用追踪 (可选)
LANGSMITH_PROJECT=easy_data_agent        # 项目名称 (可选)

# === LangGraph基础设施 ===
REDIS_URI=redis://redis:6379             # Redis连接 (必需)
DATABASE_URI=postgres://postgres:postgres@postgres:5432/langgraph  # PostgreSQL (必需)

# === 业务数据库 (MySQL) ===
HOST=mysql                              # MySQL主机
USER=gufang2020                         # MySQL用户名
MYSQL_PW=gufang2020                     # MySQL密码
DB_NAME=test                            # 数据库名
MYSQL_PORT=3306                         # MySQL端口

# === 系统配置 ===
PUBLIC_DIR=/app/shared/public           # 共享文件目录
PROJECT_ROOT=/app                       # 项目根目录
```

## 📊 使用示例 | Usage Examples

### **数据分析对话示例**

```
用户: 你好，我想分析一下我的销售数据
Agent: 你好！我是EasyDataAgent，您的专业数据分析顾问。我可以帮您：
       📊 数据预览和质量检查
       📈 生成各种可视化图表  
       🤖 构建预测模型
       💾 导出分析结果
       
       请先告诉我您的数据在哪里？是CSV文件还是数据库中？

用户: 数据在MySQL数据库的sales表中
Agent: 我来帮您提取销售数据并进行分析...
       [执行SQL查询，加载数据]
       
用户: 生成一个销售趋势图
Agent: 我来为您生成销售趋势图...
       [生成名为 sales_trend.png 的图表]
       
       ![销售趋势图](images/sales_trend.png)
       
       从图表可以看出您的销售呈现上升趋势...
```

### **功能展示**

- **智能数据预览**: 自动分析数据结构、缺失值、数据类型
- **SQL查询**: 支持复杂的JOIN、聚合、筛选操作
- **可视化**: 散点图、柱状图、热力图、时间序列图等
- **机器学习**: 分类、回归、聚类、特征工程
- **导出功能**: Excel、JSON、PDF格式导出

## 🐳 Docker服务详解 | Docker Services

### **完整架构 (开发环境)**

```yaml
services:
  redis:          # LangGraph任务队列
    image: redis:6
    ports: ["6379:6379"]
    
  postgres:       # LangGraph状态存储
    image: postgres:16
    ports: ["5432:5432"]
    
  mysql:          # 业务数据存储
    image: mysql:8.0  
    ports: ["3306:3306"]
    
  backend:        # AI代理服务
    image: gugu689/data_agent:latest
    ports: ["8123:8000"]
    volumes: 
      - shared_public:/app/shared/public
    
  frontend:       # Web界面
    build: ./frontend
    ports: ["3000:3000"]
    volumes:
      - shared_public:/app/public
```

### **共享存储说明**

- **shared_public volume**: 前后端共享的文件存储
  - `images/` - 生成的图表文件
  - `exports/` - 导出的数据文件
  - `uploads/` - 上传的文件

## 🔧 故障排除 | Troubleshooting

### **常见问题解决**

```bash
# 1. 检查服务状态
docker-compose ps
docker-compose logs backend

# 2. 端口冲突解决
# 修改 docker-compose.yml 中的端口映射
ports:
  - "3001:3000"  # 前端改为3001
  - "8124:8000"  # 后端改为8124

# 3. API密钥错误
# 检查 .env 文件中的API密钥格式
echo $OPENAI_API_KEY

# 4. 数据库连接问题
# 等待健康检查通过
docker-compose logs mysql
docker-compose logs postgres

# 5. 图片不显示问题
# 重启前端容器刷新静态文件缓存
docker-compose restart frontend

# 6. 清理并重新构建
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

### **日志分析**

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看最近的错误
docker-compose logs --tail=50 backend | grep -i error
```

### **性能优化**

```bash
# 1. 监控资源使用
docker stats

# 2. 调整内存限制 (docker-compose.yml)
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

# 3. 使用更快的模型
MODEL_NAME=gpt-3.5-turbo  # 更快更便宜
```

## 🔒 安全建议 | Security Recommendations

### **生产环境安全配置**

```bash
# 1. 使用强密码
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# 2. 限制网络访问
# 在docker-compose.prod.yml中不暴露数据库端口
services:
  mysql:
    # ports: ["3306:3306"]  # 注释掉这行
    networks:
      - internal  # 仅内部网络访问

# 3. 使用Docker Secrets
echo "your-api-key" | docker secret create openai_api_key -
```

### **数据安全**

- **本地部署**: 数据完全保留在您的基础设施中
- **加密传输**: HTTPS/WSS连接
- **访问控制**: 容器网络隔离
- **日志脱敏**: 敏感信息不记录在日志中

## 📚 扩展开发 | Extension Development

### **添加自定义工具**

```python
# 在 backend/graph.py 中添加新工具
from langchain_core.tools import tool

@tool
def custom_analysis_tool(data: str) -> str:
    """自定义分析工具"""
    # 您的分析逻辑
    return "分析结果"

# 将工具添加到工具列表
tools = [
    sql_inter,
    python_inter, 
    fig_inter,
    # ... 其他工具
    custom_analysis_tool,  # 新工具
]
```

### **自定义提示词**

```bash
# 编辑系统提示词
vim backend/prompt.txt

# 重新构建镜像
cd backend
uv run langgraph build --tag custom-agent:latest
```

## 🤝 贡献指南 | Contributing

1. **Fork** 仓库
2. **创建功能分支**: `git checkout -b feature/new-feature`
3. **提交更改**: `git commit -m 'Add new feature'`
4. **推送分支**: `git push origin feature/new-feature`
5. **创建Pull Request**

## 📄 许可证 | License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢 | Acknowledgments

- **LangGraph** - AI代理框架
- **LangChain** - 工具链生态
- **OpenAI** - 语言模型服务
- **Next.js** - 前端框架
- **Agent Chat UI** - 对话界面组件

---

## 📞 支持 | Support

- **文档**: [项目Wiki](https://github.com/your-username/EasyDataAgent/wiki)
- **问题反馈**: [GitHub Issues](https://github.com/your-username/EasyDataAgent/issues)
- **讨论交流**: [GitHub Discussions](https://github.com/your-username/EasyDataAgent/discussions)

---

**⭐ 如果这个项目对您有帮助，请给个星标支持！**

*Made with ❤️ by the EasyDataAgent Team*
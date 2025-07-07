# EasyDataAgent

A powerful and secure data analysis agent that combines **fast development** with **data security**. Built with LangGraph and modern web technologies, EasyDataAgent enables rapid deployment of AI-powered data analysis applications with complete control over your data.

## Key Features

- **Fast Development**: Deploy a complete data analysis agent in minutes
- **Data Security**: Connect to your own databases with full control over data access
- **Local Deployment**: Run entirely on your infrastructure
- **Comprehensive Analysis**: SQL queries, data visualization, statistical analysis, and web search
- **Modern UI**: Beautiful, responsive chat interface for natural language interactions
- **Multi-format Export**: Generate charts and export data in various formats

## Tech Stack

### Backend (LangGraph)
- **LangGraph**: Agent orchestration and workflow management
- **LangChain**: LLM integration and tool management
- **DeepSeek**: High-performance language model
- **Python**: Core backend language
- **PyMySQL**: MySQL database connectivity
- **Pandas**: Data manipulation and analysis
- **Matplotlib/Seaborn**: Data visualization
- **Tavily**: Web search capabilities

### Frontend (Agent Chat UI)
- **Next.js 15**: React framework with server-side rendering
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Framer Motion**: Smooth animations and transitions
- **React Markdown**: Rich text rendering with math support

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL database
- Environment variables configured

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/EasyDataAgent.git
cd EasyDataAgent
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```env
HOST=your-mysql-host
USER=your-mysql-user
MYSQL_PW=your-mysql-password
DB_NAME=your-database-name
PORT=3306
DEEPSEEK_API_KEY=your-deepseek-api-key
TAVILY_API_KEY=your-tavily-api-key
```

4. Start the LangGraph server:
```bash
langgraph dev
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd agent-chat-ui-main
```

2. Install dependencies:
```bash
pnpm install
```

3. Start the development server:
```bash
pnpm dev
```

4. Open your browser to `http://localhost:3000`

## Core Capabilities

### 1. Database Operations
- **SQL Queries**: Execute complex SQL queries with natural language
- **Data Extraction**: Import database tables into Python environment
- **Secure Connections**: Direct connection to your MySQL databases

### 2. Data Analysis
- **Statistical Analysis**: Comprehensive statistical computations
- **Data Processing**: Clean, transform, and manipulate datasets
- **Python Execution**: Run custom Python code for advanced analysis

### 3. Visualization
- **Interactive Charts**: Generate publication-ready visualizations
- **Multiple Formats**: Support for various chart types and export formats
- **Real-time Rendering**: Instant visualization updates

### 4. Web Intelligence
- **Real-time Search**: Access current information via web search
- **Contextual Results**: Relevant information retrieval for analysis tasks


## Security Features

- **Local Data Control**: Your data never leaves your infrastructure
- **Secure Database Connections**: Encrypted connections to your databases
- **Environment-based Configuration**: Sensitive credentials stored securely
- **No Data Leakage**: Analysis performed locally without external data transmission

## Development Benefits

### Rapid Prototyping
- **Zero Configuration**: Works out-of-the-box with minimal setup
- **Instant Deployment**: Deploy locally in minutes
- **Flexible Integration**: Easy to integrate with existing systems

### Scalable Architecture
- **Modular Design**: Easy to extend and customize
- **Production Ready**: Built with enterprise-grade technologies
- **Performance Optimized**: Efficient processing of large datasets

## Use Cases

- **Business Intelligence**: Create interactive dashboards and reports
- **Data Science**: Perform exploratory data analysis and modeling
- **Research**: Conduct statistical analysis and generate insights
- **Monitoring**: Build real-time data monitoring systems
- **Education**: Teach data analysis concepts interactively

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
HOST=localhost
USER=your_username
MYSQL_PW=your_password
DB_NAME=your_database
PORT=3306

# API Keys
DEEPSEEK_API_KEY=your_deepseek_key
TAVILY_API_KEY=your_tavily_key

# Optional: LangSmith for debugging
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
```

### Database Setup

Ensure your MySQL database is accessible and contains the tables you want to analyze. The agent will automatically connect using the provided credentials.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the configuration guide

---

**EasyDataAgent** - Simple development, secure data, powerful analysis.
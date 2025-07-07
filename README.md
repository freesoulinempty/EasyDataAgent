# EasyDataAgent

A data analysis agent for fast development and secure local deployment. Analyze CSV files, generate machine learning code, create visualizations, and query databases through natural language.

## Features

- **CSV Data Analysis**: Load and analyze CSV files with pandas
- **Machine Learning**: Generate ML code for classification, regression, clustering
- **Data Visualization**: Create charts and plots with matplotlib/seaborn
- **Database Integration**: Query MySQL databases securely
- **Code Generation**: Execute Python code for data processing
- **Web Search**: Access real-time information

## Tech Stack

**Backend**: LangGraph, LangChain, DeepSeek, Python, pandas, matplotlib, PyMySQL  
**Frontend**: agent-chat-ui

## Quick Start

### Backend Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment (.env):
```env
HOST=your-mysql-host
USER=your-mysql-user  
MYSQL_PW=your-mysql-password
DB_NAME=your-database-name
PORT=3306
DEEPSEEK_API_KEY=your-deepseek-key
TAVILY_API_KEY=your-tavily-key
```

3. Start LangGraph server:
```bash
langgraph dev
```

### Frontend Setup

1. Install and start:
```bash
cd agent-chat-ui-main
pnpm install
pnpm dev
```

2. Open http://localhost:3000

## Core Capabilities

### Data Analysis
- Load CSV files for analysis
- Statistical computations and data cleaning
- Exploratory data analysis (EDA)

### Machine Learning
- Classification and regression models
- Clustering and dimensionality reduction
- Model evaluation and performance metrics

### Visualization
- Statistical plots and distributions
- Interactive charts and dashboards
- Export charts in multiple formats

### Database Operations
- SQL query execution
- Data extraction to pandas DataFrames
- Secure local database connections

## Example Use Cases

- Analyze customer data from CSV files
- Build predictive models
- Create business intelligence dashboards
- Perform statistical analysis
- Generate automated reports

## Security

- Local deployment only
- Your data stays on your infrastructure
- Secure database connections
- No external data transmission

## Configuration

Create `.env` file:
```env
# Database
HOST=localhost
USER=your_username
MYSQL_PW=your_password
DB_NAME=your_database
PORT=3306

# API Keys
DEEPSEEK_API_KEY=your_key
TAVILY_API_KEY=your_key
```

## License

MIT License

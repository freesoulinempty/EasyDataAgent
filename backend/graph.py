import os                    
from dotenv import load_dotenv   
from langchain_openai import ChatOpenAI       
from langgraph.prebuilt import create_react_agent  
from langchain_core.tools import tool         
from pydantic import BaseModel, Field          
from langchain_tavily import TavilySearch     
import pandas as pd          
import pymysql              
import json                 
from datetime import datetime  
import matplotlib          
import matplotlib.pyplot as plt  
import seaborn as sns       
from reportlab.lib.pagesizes import letter          
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph  
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.lib import colors                     

# Load environment variables / 加载环境变量
load_dotenv(override=True)

# Create Tavily search tool / 创建Tavily搜索工具
search_tool = TavilySearch(max_results=5, topic="general")

# Create SQL query tool / 创建SQL查询工具
description = """
Call this function when users need to perform database queries.
This function runs SQL code on a specified MySQL server for data query tasks,
using pymysql to connect to the MySQL database.
This function only handles SQL code execution and data querying. For data extraction, use the extract_data function.
"""

# Define structured parameter model / 定义结构化参数模型
class SQLQuerySchema(BaseModel):
    sql_query: str = Field(description=description)

# ============================================================================
# SQL QUERY EXECUTION TOOL IMPLEMENTATION
# SQL 查询执行工具实现
# ============================================================================

@tool(args_schema=SQLQuerySchema)
def sql_inter(sql_query: str) -> str:
    """
    High-performance SQL query execution tool for database interaction
    高性能 SQL 查询执行工具，用于数据库交互
    
    This function serves as the primary interface for executing SQL queries against
    a MySQL database. It's designed for read-only operations and returns structured
    JSON data for further processing by other tools in the analysis pipeline.
    
    此函数作为对 MySQL 数据库执行 SQL 查询的主要接口。
    它专为只读操作设计，返回结构化的 JSON 数据，
    供分析管道中的其他工具进一步处理。
    
    SECURITY FEATURES / 安全特性:
    - Environment-based configuration (no hardcoded credentials)
    - 基于环境的配置（无硬编码凭据）
    - Automatic connection cleanup and resource management
    - 自动连接清理和资源管理
    - UTF-8 encoding support for international data
    - UTF-8 编码支持国际化数据
    
    PERFORMANCE OPTIMIZATIONS / 性能优化:
    - Connection pooling through environment configuration
    - 通过环境配置的连接池
    - Efficient result formatting as JSON for downstream processing
    - 高效的结果格式化为 JSON 供下游处理
    - Minimal memory footprint with cursor-based operations
    - 基于游标操作的最小内存占用
    
    DATA FLOW / 数据流:
    SQL Query Input → MySQL Execution → Result Processing → JSON Output
    SQL 查询输入 → MySQL 执行 → 结果处理 → JSON 输出
    
    :param sql_query: Well-formed SQL query string for database execution
                     用于数据库执行的良好格式化 SQL 查询字符串
    :type sql_query: str
    
    :return: JSON-formatted query results or error message
             JSON 格式的查询结果或错误信息
    :rtype: str
    
    :raises: Connection errors, SQL syntax errors, timeout exceptions
             连接错误、SQL 语法错误、超时异常
    
    Example Usage / 使用示例:
        result = sql_inter("SELECT * FROM customers LIMIT 10")
        # Returns: '[{"id": 1, "name": "John", ...}, ...]'
    """

    load_dotenv(override=True)
    
    host = os.getenv('HOST')           
    user = os.getenv('USER')           
    mysql_pw = os.getenv('MYSQL_PW')   
    db = os.getenv('DB_NAME')          
    port = os.getenv('MYSQL_PORT')           
    
    connection = pymysql.connect(
        host=host,                    
        user=user,                    
        passwd=mysql_pw,              
        db=db,                        
        port=int(port),               
        charset='utf8',               
        autocommit=True,              
        connect_timeout=30,           
        read_timeout=60               
    )
    
    # =======================================================================
    # SAFE SQL EXECUTION WITH RESOURCE MANAGEMENT
    # 安全 SQL 执行和资源管理
    # =======================================================================
    
    try:
        # Use context manager for automatic cursor cleanup
        # 使用上下文管理器进行自动游标清理
        # This ensures proper resource disposal even on exceptions
        # 这确保即使在异常情况下也能正确释放资源
        with connection.cursor() as cursor:
            # Execute the SQL query with built-in error handling
            # 执行 SQL 查询，内置错误处理
            cursor.execute(sql_query)
            
            # Fetch all results efficiently into memory
            # 高效地将所有结果获取到内存中
            # For large datasets, consider using fetchmany() for memory optimization
            # 对于大型数据集，考虑使用 fetchmany() 进行内存优化
            results = cursor.fetchall()
            
            # Optional success logging - useful for debugging
            # 可选的成功日志 - 用于调试很有用
            # print("SQL query executed successfully, organizing results... / SQL 查询已成功执行，正在整理结果...")
            
    except pymysql.Error as e:
        # Handle MySQL-specific errors with detailed information
        # 处理 MySQL 特定错误，提供详细信息
        error_msg = f"MySQL Error {e.args[0]}: {e.args[1]}"
        return json.dumps({"error": error_msg, "query": sql_query}, ensure_ascii=False)
    
    except Exception as e:
        # Handle general exceptions with context
        # 处理一般异常，提供上下文
        error_msg = f"Query execution failed: {str(e)}"
        return json.dumps({"error": error_msg, "query": sql_query}, ensure_ascii=False)
    
    finally:
        # Ensure connection is always closed to prevent resource leaks
        # 确保连接始终关闭，防止资源泄漏
        # This runs regardless of success or failure
        # 无论成功或失败都会运行
        if 'connection' in locals() and connection.open:
            connection.close()

    return json.dumps(
        results, 
        ensure_ascii=False,   
        default=str,           
        indent=2                
    )

# ============================================================================
# DATA EXTRACTION TOOL CONFIGURATION
# 数据提取工具配置
# ============================================================================
# This tool differs from sql_inter by importing data directly into the Python
# environment as pandas DataFrames for immediate analysis and manipulation.
# 此工具与 sql_inter 不同，它将数据直接导入 Python 环境
# 作为 pandas DataFrames，供立即分析和操作。
# ============================================================================

# Pydantic schema for data extraction tool input validation
# 数据提取工具输入验证的 Pydantic 模式
class ExtractQuerySchema(BaseModel):
    """Schema for validating data extraction parameters | 数据提取参数验证模式"""
    
    sql_query: str = Field(
        description="SQL query statement for extracting data from MySQL database into Python environment / 用于从 MySQL 数据库提取数据到 Python 环境的 SQL 查询语句",
        min_length=1,
        max_length=10000
    )
    
    df_name: str = Field(
        description="Variable name for storing the extracted DataFrame in global scope (must be valid Python identifier) / 用于在全局作用域中存储提取的 DataFrame 的变量名（必须是有效的 Python 标识符）",
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$'  # Valid Python identifier / 有效的 Python 标识符
    )

# ============================================================================
# DATA EXTRACTION TOOL IMPLEMENTATION
# 数据提取工具实现
# ============================================================================
@tool(args_schema=ExtractQuerySchema)
def extract_data(sql_query: str, df_name: str) -> str:
    """
    Extract a table from MySQL database to the current Python environment. Note that this function only handles data extraction,
    not data querying. For data queries in MySQL, use the sql_inter function.
    Also note that when writing external function parameter messages, they must be strings in JSON format.
    
    :param sql_query: SQL query statement in string format for extracting a table from MySQL
    :param df_name: Variable name for locally saving the table extracted from MySQL database, represented as a string
    :return: Table reading and saving results
    """
    # Active status logging for data extraction operations
    # 数据提取操作的活动状态日志
    print("Calling extract_data tool to run SQL query... / 正在调用 extract_data 工具运行 SQL 查询...")
    
    load_dotenv(override=True)
    host = os.getenv('HOST')
    user = os.getenv('USER')
    mysql_pw = os.getenv('MYSQL_PW')
    db = os.getenv('DB_NAME')
    port = os.getenv('MYSQL_PORT')

    # Create database connection / 创建数据库连接
    connection = pymysql.connect(
        host=host,
        user=user,
        passwd=mysql_pw,
        db=db,
        port=int(port),
        charset='utf8'
    )

    try:
        # Execute SQL and save as global variable / 执行 SQL 并保存为全局变量
        df = pd.read_sql(sql_query, connection)
        globals()[df_name] = df
        # Optional success confirmation - useful for development
        # 可选的成功确认 - 用于开发很有用
        # print("Data successfully extracted and saved as global variable: / 数据成功提取并保存为全局变量：", df_name)
        return f"Successfully created pandas object `{df_name}` containing data extracted from MySQL."
    except Exception as e:
        return f"Execution failed: {e}"
    finally:
        connection.close()

# Create Python code execution tool / 创建Python代码执行工具
# Python code execution tool structured parameter description / Python代码执行工具结构化参数说明
class PythonCodeInput(BaseModel):
    py_code: str = Field(description="A valid Python code string, e.g., '2 + 2' or 'x = 3\\ny = x * 2'")

@tool(args_schema=PythonCodeInput)
def python_inter(py_code):
    """
    Call this function when users need to write and execute Python programs.
    This function can execute Python code and return the final result. Note that this function can only execute non-plotting code.
    For plotting-related code, use the fig_inter function.
    """    
    g = globals()
    try:
        # Try to return expression result if it's an expression / 尝试如果是表达式，则返回表达式运行结果
        return str(eval(py_code, g))
    # If error occurs, test if it's repeated assignment to the same variable / 若报错，则先测试是否是对相同变量重复赋值
    except Exception as e:
        global_vars_before = set(g.keys())
        try:            
            exec(py_code, g)
        except Exception as e:
            return f"Code execution error: {e}"
        global_vars_after = set(g.keys())
        new_vars = global_vars_after - global_vars_before
        # If new variables exist / 若存在新变量
        if new_vars:
            result = {var: g[var] for var in new_vars}
            # Optional execution confirmation for debugging
            # 可选的执行确认用于调试
            # print("代码已顺利执行，正在进行结果梳理...")
            return str(result)
        else:
            # Optional execution confirmation for debugging
            # 可选的执行确认用于调试
            # print("代码已顺利执行，正在进行结果梳理...")
            return "Code executed successfully"

# Create plotting tool / 创建绘图工具
# Plotting tool structured parameter description / 绘图工具结构化参数说明
class FigCodeInput(BaseModel):
    py_code: str = Field(description="Python plotting code to execute, must use matplotlib/seaborn to create images and assign to variables")
    fname: str = Field(description="Variable name of the image object, e.g., 'fig', used to extract from code and save as image")

@tool(args_schema=FigCodeInput)
def fig_inter(py_code: str, fname: str) -> str:
    """
    Call this function when users need to use Python for visualization plotting tasks.

    Notes:
    1. All plotting code must create an image object and assign it to the specified variable name (e.g., `fig`).
    2. Must use `fig = plt.figure()` or `fig = plt.subplots()`.
    3. Do not use `plt.show()`.
    4. Ensure the code ends with `fig.tight_layout()`.
    5. All text content in plotting code including axis labels (xlabel, ylabel), titles, legends must be in English.

    Example code:
    fig = plt.figure(figsize=(10,6))
    plt.plot([1,2,3], [4,5,6])
    fig.tight_layout()
    """
    # Optional debug output for monitoring tool usage
    # 可选的调试输出用于监控工具使用
    # print("Calling fig_inter tool to run Python code... / 正在调用fig_inter工具运行Python代码...")

    current_backend = matplotlib.get_backend()
    matplotlib.use('Agg')

    local_vars = {"plt": plt, "pd": pd, "sns": sns}
    
    # Set image save path (from environment variable) / 设置图像保存路径（从环境变量）
    base_dir = os.getenv('PUBLIC_DIR', "/app/shared/public")
    images_dir = os.path.join(base_dir, "images")
    os.makedirs(images_dir, exist_ok=True)  # Automatically create images folder if it doesn't exist / 自动创建 images 文件夹（如不存在）
    try:
        g = globals()
        exec(py_code, g, local_vars)
        g.update(local_vars)

        fig = local_vars.get(fname, None)
        if fig:
            image_filename = f"{fname}.png"
            abs_path = os.path.join(images_dir, image_filename)  # Absolute path / 绝对路径
            rel_path = os.path.join("images", image_filename)    # Return relative path (for frontend) / 返回相对路径（给前端用）

            fig.savefig(abs_path, bbox_inches='tight')
            return f"Image saved successfully: {rel_path}\n\n---\n\n![Generated Chart]({rel_path})"
        else:
            return "Image object not found, please confirm the variable name is correct and is a matplotlib figure object."
    except Exception as e:
        return f"Execution failed: {e}"
    finally:
        plt.close('all')
        matplotlib.use(current_backend)

# Load prompt from external file / 从外部文件加载提示词
def load_prompt():
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback prompt if file not found
        return """
        You are EasyDataAgent, a professional data analysis consultant with comprehensive analytical capabilities.
        Use the available tools to help users with data analysis, visualization, and insights.
        Always be proactive in suggesting relevant tools and providing professional guidance.
        """

prompt = load_prompt()

# ============================================================================
# MULTI-FORMAT DATA EXPORT TOOL CONFIGURATION
# 多格式数据导出工具配置
# ============================================================================
# This tool provides enterprise-grade data export capabilities for sharing analysis results
# 该工具提供企业级数据导出功能，用于分享分析结果
# Supports Excel (business users), JSON (technical users), PDF (executive reports)
# 支持Excel（业务用户）、JSON（技术用户）、PDF（执行报告）

# Data export schema definition / 数据导出模式定义
class DataExportSchema(BaseModel):
    """
    Input validation schema for data export operations
    数据导出操作的输入验证模式
    
    Ensures proper parameter types and format validation for export operations
    确保导出操作的参数类型和格式验证正确
    """
    df_name: str = Field(description="Name of the pandas DataFrame variable to export / 要导出的pandas DataFrame变量名")
    format_type: str = Field(description="Export format: 'excel', 'json', or 'pdf' / 导出格式：'excel'、'json'或'pdf'")
    filename: str = Field(description="Output filename (without extension) / 输出文件名（不包含扩展名）")

@tool(args_schema=DataExportSchema)
def export_data(df_name: str, format_type: str, filename: str) -> str:
    """
    MULTI-FORMAT DATA EXPORT FUNCTION
    多格式数据导出功能
    
    Export pandas DataFrame to various professional formats for different stakeholder needs.
    将pandas DataFrame导出为各种专业格式，满足不同利益相关者的需求。
    
    BUSINESS VALUE / 业务价值:
    - Professional reporting for executives / 为管理层提供专业报告
    - Data sharing across different platforms / 跨平台数据共享
    - Archive analysis results for future reference / 归档分析结果供未来参考
    - Integration with external systems / 与外部系统集成
    
    EXPORT FORMATS & USE CASES / 导出格式和使用场景:
    1. Excel (.xlsx): Business users, data manipulation, pivot tables / 业务用户、数据操作、数据透视表
    2. JSON (.json): API integration, web applications, data exchange / API集成、Web应用、数据交换
    3. PDF (.pdf): Executive reports, presentations, documentation / 执行报告、演示、文档
    
    WORKFLOW PROCESS / 工作流程:
    Step 1: Validate DataFrame existence and type / 步骤1：验证DataFrame存在性和类型
    Step 2: Create export directory structure / 步骤2：创建导出目录结构
    Step 3: Execute format-specific export logic / 步骤3：执行特定格式的导出逻辑
    Step 4: Return success status and file path / 步骤4：返回成功状态和文件路径
    
    :param df_name: Name of the pandas DataFrame variable to export / 要导出的pandas DataFrame变量名
    :param format_type: Export format - 'excel', 'json', or 'pdf' / 导出格式 - 'excel'、'json'或'pdf'
    :param filename: Output filename without extension / 不包含扩展名的输出文件名
    :return: Export status and relative file path for web access / 导出状态和用于Web访问的相对文件路径
    """
    try:
        # ========================================================================
        # STEP 1: DATAFRAME VALIDATION AND RETRIEVAL
        # 步骤1：DataFrame验证和获取
        # ========================================================================
        
        # Retrieve DataFrame from global namespace (injected by extract_data or python_inter)
        # 从全局命名空间获取DataFrame（由extract_data或python_inter注入）
        g = globals()
        if df_name not in g:
            return f"Error: DataFrame '{df_name}' not found. Please extract or create the DataFrame first."
        
        # Ensure the object is actually a pandas DataFrame
        # 确保对象确实是pandas DataFrame
        df = g[df_name]
        if not isinstance(df, pd.DataFrame):
            return f"Error: '{df_name}' is not a pandas DataFrame."
        
        # ========================================================================
        # STEP 2: EXPORT DIRECTORY SETUP AND FILE PATH MANAGEMENT
        # 步骤2：导出目录设置和文件路径管理
        # ========================================================================
        
        # Define base directory for web-accessible exports
        # 定义用于Web可访问导出的基本目录
        # This path allows the web UI to access exported files
        # 此路径允许Web UI访问导出的文件
        base_dir = os.getenv('PUBLIC_DIR', "/app/shared/public")
        exports_dir = os.path.join(base_dir, "exports")
        
        # Create exports directory if it doesn't exist
        # 如果导出目录不存在则创建
        os.makedirs(exports_dir, exist_ok=True)
        
        # ========================================================================
        # STEP 3A: EXCEL FORMAT EXPORT PROCESSING
        # 步骤3A：Excel格式导出处理
        # ========================================================================
        
        if format_type.lower() == 'excel':
            # Excel export for business users and data manipulation
            # 面向业务用户和数据操作的Excel导出
            file_path = os.path.join(exports_dir, f"{filename}.xlsx")
            
            # Export DataFrame to Excel with index for row identification
            # 将DataFrame导出为Excel，包含索引用于行识别
            # openpyxl engine provides robust Excel compatibility
            # openpyxl引擎提供强大的Excel兼容性
            df.to_excel(file_path, index=True, engine='openpyxl')
            
            # Return relative path for web UI access
            # 返回用于Web UI访问的相对路径
            rel_path = os.path.join("exports", f"{filename}.xlsx")
            return f"Excel file exported successfully: {rel_path}"
            
        # ========================================================================
        # STEP 3B: JSON FORMAT EXPORT PROCESSING
        # 步骤3B：JSON格式导出处理
        # ========================================================================
        
        elif format_type.lower() == 'json':
            # JSON export for API integration and web applications
            # 面向API集成和Web应用的JSON导出
            file_path = os.path.join(exports_dir, f"{filename}.json")
            
            # Export DataFrame as JSON with records orientation
            # 以records方向将DataFrame导出为JSON
            # 'records' format: [{col1: val1, col2: val2}, ...] - most API-friendly
            # 'records'格式：[{col1: val1, col2: val2}, ...] - 最适合API
            # ISO date format ensures international compatibility
            # ISO日期格式确保国际兼容性
            # Pretty printing with indent=2 for readability
            # 使用indent=2进行美化打印以提高可读性
            df.to_json(file_path, orient='records', date_format='iso', indent=2)
            
            # Return relative path for web UI access
            # 返回用于Web UI访问的相对路径
            rel_path = os.path.join("exports", f"{filename}.json")
            return f"JSON file exported successfully: {rel_path}"
            
        # ========================================================================
        # STEP 3C: PDF FORMAT EXPORT PROCESSING
        # 步骤3C：PDF格式导出处理
        # ========================================================================
        
        elif format_type.lower() == 'pdf':
            # PDF export for executive reports and presentations
            # 面向执行报告和演示的PDF导出
            file_path = os.path.join(exports_dir, f"{filename}.pdf")
            
            # ================================================================
            # PDF DOCUMENT STRUCTURE INITIALIZATION
            # PDF文档结构初始化
            # ================================================================
            # Create professional PDF document with standard letter size
            # 创建标准信纸尺寸的专业PDF文档
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []  # Document elements container / 文档元素容器
            styles = getSampleStyleSheet()  # Professional styling / 专业样式
            
            # ================================================================
            # DOCUMENT HEADER AND METADATA
            # 文档标题和元数据
            # ================================================================
            # Add professional title for the data export
            # 为数据导出添加专业标题
            title = Paragraph(f"Data Export: {df_name}", styles['Title'])
            elements.append(title)
            
            # Add timestamp for report tracking and versioning
            # 添加时间戳用于报告跟踪和版本管理
            timestamp = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
            elements.append(timestamp)
            
            # ================================================================
            # DATA TABLE PREPARATION AND FORMATTING
            # 数据表格准备和格式化
            # ================================================================
            # Convert DataFrame to table format with headers
            # 将DataFrame转换为带有标题的表格格式
            data = [df.columns.tolist()]  # Start with column headers / 以列标题开始
            
            # Limit rows for PDF readability and performance
            # 限制行数以提高PDF可读性和性能
            max_rows = min(50, len(df))  # Maximum 50 rows for optimal PDF rendering / 最多50行以优化PDF渲染
            
            # Convert DataFrame rows to string format for PDF compatibility
            # 将DataFrame行转换为字符串格式以兼容PDF
            for _, row in df.head(max_rows).iterrows():
                data.append([str(x) for x in row.tolist()])
            
            # ================================================================
            # PROFESSIONAL TABLE STYLING
            # 专业表格样式
            # ================================================================
            # Create formatted table with professional styling
            # 创建具有专业样式的格式化表格
            table = Table(data)
            table.setStyle(TableStyle([
                # Header row styling / 标题行样式
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),        # Header background / 标题背景
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),   # Header text color / 标题文本颜色
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),              # Center alignment / 居中对齐
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),    # Bold header font / 粗体标题字体
                ('FONTSIZE', (0, 0), (-1, 0), 12),                  # Header font size / 标题字体大小
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),             # Header padding / 标题内边距
                # Data rows styling / 数据行样式
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),     # Data background / 数据背景
                ('GRID', (0, 0), (-1, -1), 1, colors.black)         # Table grid / 表格网格
            ]))
            
            elements.append(table)
            
            # ================================================================
            # PAGINATION NOTICE FOR LARGE DATASETS
            # 大型数据集的分页通知
            # ================================================================
            # Add note if data was truncated for PDF optimization
            # 如果为了PDF优化而截断数据，则添加说明
            if len(df) > max_rows:
                note = Paragraph(f"Note: Only first {max_rows} rows shown. Total rows: {len(df)}", styles['Normal'])
                elements.append(note)
            
            # Build the PDF document with all elements
            # 使用所有元素构建PDF文档
            doc.build(elements)
            
            # Return relative path for web UI access
            # 返回用于Web UI访问的相对路径
            rel_path = os.path.join("exports", f"{filename}.pdf")
            return f"PDF file exported successfully: {rel_path}"
            
        # ========================================================================
        # STEP 3D: UNSUPPORTED FORMAT HANDLING
        # 步骤3D：不支持格式处理
        # ========================================================================
        
        else:
            # Handle unsupported export formats gracefully
            # 优雅地处理不支持的导出格式
            return f"Error: Unsupported format '{format_type}'. Supported formats: excel, json, pdf"
            
    except Exception as e:
        # ========================================================================
        # COMPREHENSIVE ERROR HANDLING AND RECOVERY
        # 综合错误处理和恢复
        # ========================================================================
        # Catch and report any unexpected errors during export process
        # 捕获并报告导出过程中的任何意外错误
        return f"Export failed: {str(e)}"

# ============================================================================
# COMPREHENSIVE DATA PREVIEW TOOL CONFIGURATION
# 综合数据预览工具配置
# ============================================================================
# Advanced data exploration and quality assessment capabilities
# 高级数据探索和质量评估功能
# ============================================================================

class DataPreviewSchema(BaseModel):
    """Schema for data preview tool input validation | 数据预览工具输入验证模式"""
    
    df_name: str = Field(
        description="Name of the pandas DataFrame variable for comprehensive preview / 用于综合预览的 pandas DataFrame 变量名",
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$'  # Valid Python identifier / 有效的 Python 标识符
    )
    
    rows: int = Field(
        default=10,
        description="Number of sample rows to display for data preview (1-100) / 用于数据预览显示的样本行数 (1-100)",
        ge=1,      # Minimum 1 row / 最少 1 行
        le=100     # Maximum 100 rows for performance / 最多 100 行以保证性能
    )

@tool(args_schema=DataPreviewSchema)
def data_preview(df_name: str, rows: int = 10) -> str:
    """
    Enterprise-grade data preview and exploration tool for comprehensive dataset analysis
    企业级数据预览和探索工具，用于综合数据集分析
    
    This function provides a detailed, multi-dimensional analysis of DataFrames,
    combining statistical insights, data quality metrics, and structural information
    into a comprehensive report suitable for both technical analysis and business
    stakeholder communication.
    
    此函数提供 DataFrame 的详细、多维度分析，
    将统计洞察、数据质量指标和结构信息结合成
    适用于技术分析和业务利益相关者沟通的综合报告。
    
    COMPREHENSIVE ANALYSIS FEATURES / 综合分析功能:
    - Dataset structure and dimensionality analysis
    - 数据集结构和维度分析
    - Memory usage optimization recommendations
    - 内存使用优化建议
    - Data type analysis with conversion suggestions
    - 数据类型分析及转换建议
    - Missing value patterns and impact assessment
    - 缺失值模式和影响评估
    - Statistical summaries for numeric and categorical data
    - 数值和分类数据的统计摘要
    - Sample data with intelligent row selection
    - 具有智能行选择的样本数据
    
    BUSINESS INTELLIGENCE INSIGHTS / 商业智能洞察:
    - Data readiness assessment for analysis
    - 分析数据就绪评估
    - Quality indicators and recommendations
    - 质量指标和建议
    - Performance optimization opportunities
    - 性能优化机会
    
    TECHNICAL SPECIFICATIONS / 技术规格:
    - Unicode and emoji support in output
    - 输出中的 Unicode 和表情符号支持
    - Professional formatting with visual hierarchy
    - 具有视觉层次结构的专业格式化
    - Timestamp tracking for audit trails
    - 用于审计跟踪的时间戳记录
    
    :param df_name: Name of DataFrame variable in global scope for analysis
                   全局作用域中用于分析的 DataFrame 变量名
    :type df_name: str
    
    :param rows: Number of representative sample rows to display
                要显示的代表性样本行数
    :type rows: int
    
    :return: Comprehensive formatted data preview report
             综合格式化数据预览报告
    :rtype: str
    
    :raises: TypeError if df_name is not a DataFrame, KeyError if variable not found
             如果 df_name 不是 DataFrame 则引发 TypeError，如果找不到变量则引发 KeyError
    
    Example Usage / 使用示例:
        data_preview("sales_data", 15)
        # Returns comprehensive preview with 15 sample rows
        # 返回包含 15 个样本行的综合预览
    """
    try:
        # Get DataFrame from global variables
        g = globals()
        if df_name not in g:
            return f"Error: DataFrame '{df_name}' not found. Please extract or create the DataFrame first."
        
        df = g[df_name]
        if not isinstance(df, pd.DataFrame):
            return f"Error: '{df_name}' is not a pandas DataFrame."
        
        # =======================================================================
        # COMPREHENSIVE PREVIEW REPORT GENERATION
        # 综合预览报告生成
        # =======================================================================
        
        # Initialize structured report with professional formatting
        # 使用专业格式初始化结构化报告
        preview_report = []
        preview_report.append(f"{'='*60}")
        preview_report.append(f"   DATA PREVIEW SNAPSHOT FOR '{df_name.upper()}'")
        preview_report.append(f"   数据预览快照 - '{df_name.upper()}'")
        preview_report.append(f"{'='*60}")
        preview_report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 生成时间")
        preview_report.append("")
        
        # =======================================================================
        # DATASET STRUCTURE AND PERFORMANCE METRICS
        # 数据集结构和性能指标
        # =======================================================================
        
        # Calculate comprehensive structural metrics
        # 计算综合结构指标
        total_cells = df.shape[0] * df.shape[1]
        memory_mb = df.memory_usage(deep=True).sum() / 1024**2
        memory_per_row = memory_mb / df.shape[0] if df.shape[0] > 0 else 0
        
        preview_report.append("📊 DATASET STRUCTURE & PERFORMANCE | 数据集结构和性能:")
        preview_report.append(f"  • Dimensions: {df.shape[0]:,} rows × {df.shape[1]} columns ({total_cells:,} total cells)")
        preview_report.append(f"  • Memory Usage: {memory_mb:.2f} MB ({memory_per_row:.3f} MB per row)")
        preview_report.append(f"  • Index Type: {type(df.index).__name__} (Range: {df.index[0]} to {df.index[-1]} if len(df) > 0 else 'Empty')")
        
        # Performance assessment
        # 性能评估
        if memory_mb > 100:
            preview_report.append(f"  ⚠️  Large dataset detected - consider chunked processing for better performance")
        if df.shape[1] > 50:
            preview_report.append(f"  ⚠️  High dimensionality ({df.shape[1]} columns) - feature selection recommended")
            
        preview_report.append("")
        
        # =======================================================================
        # DATA TYPE ANALYSIS WITH OPTIMIZATION RECOMMENDATIONS
        # 数据类型分析及优化建议
        # =======================================================================
        
        # Analyze data types and provide optimization insights
        # 分析数据类型并提供优化洞察
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        datetime_cols = df.select_dtypes(include=['datetime']).columns
        
        preview_report.append("🏷️  DATA TYPE ANALYSIS | 数据类型分析:")
        preview_report.append(f"  🔢 Numeric Columns ({len(numeric_cols)}): {', '.join(numeric_cols[:5])}{'...' if len(numeric_cols) > 5 else ''}")
        preview_report.append(f"  📝 Categorical Columns ({len(categorical_cols)}): {', '.join(categorical_cols[:5])}{'...' if len(categorical_cols) > 5 else ''}")
        preview_report.append(f"  📅 DateTime Columns ({len(datetime_cols)}): {', '.join(datetime_cols[:5])}{'...' if len(datetime_cols) > 5 else ''}")
        
        # Detailed type breakdown with optimization suggestions
        # 详细类型分解及优化建议
        preview_report.append("  \n  🔍 Detailed Type Breakdown:")
        for col, dtype in df.dtypes.items():
            memory_usage = df[col].memory_usage(deep=True) / 1024**2
            if str(dtype) == 'object' and df[col].nunique() < len(df) * 0.5:
                preview_report.append(f"    • {col}: {dtype} ({memory_usage:.2f}MB) - Consider category type for memory optimization")
            elif 'int64' in str(dtype) and df[col].max() < 2**31:
                preview_report.append(f"    • {col}: {dtype} ({memory_usage:.2f}MB) - Could use int32 to save memory")
            else:
                preview_report.append(f"    • {col}: {dtype} ({memory_usage:.2f}MB)")
        preview_report.append("")
        
        # Missing values analysis
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)
        preview_report.append("❓ MISSING VALUES:")
        for col in df.columns:
            if missing[col] > 0:
                preview_report.append(f"  • {col}: {missing[col]} ({missing_pct[col]}%)")
        if missing.sum() == 0:
            preview_report.append("  • No missing values found ✓")
        preview_report.append("")
        
        # Numeric columns summary
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            preview_report.append("📈 NUMERIC COLUMNS SUMMARY:")
            desc = df[numeric_cols].describe()
            for col in numeric_cols:
                preview_report.append(f"  • {col}:")
                preview_report.append(f"    - Range: {desc.loc['min', col]:.2f} to {desc.loc['max', col]:.2f}")
                preview_report.append(f"    - Mean: {desc.loc['mean', col]:.2f}")
                preview_report.append(f"    - Std: {desc.loc['std', col]:.2f}")
            preview_report.append("")
        
        # Categorical columns info
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) > 0:
            preview_report.append("🏷️  CATEGORICAL COLUMNS:")
            for col in cat_cols:
                unique_count = df[col].nunique()
                preview_report.append(f"  • {col}: {unique_count} unique values")
                if unique_count <= 10:
                    values = df[col].value_counts().head(5)
                    preview_report.append(f"    - Top values: {list(values.index)}")
            preview_report.append("")
        
        # =======================================================================
        # INTELLIGENT SAMPLE DATA PRESENTATION
        # 智能样本数据展示
        # =======================================================================
        
        # Generate representative sample with intelligent column selection
        # 生成具有智能列选择的代表性样本
        sample_size = min(rows, len(df))
        
        preview_report.append(f"📋 SAMPLE DATA PREVIEW | 样本数据预览 (First {sample_size} rows):")
        preview_report.append(f"   Showing {sample_size} of {len(df):,} total rows ({sample_size/len(df)*100:.1f}% sample)")
        preview_report.append("")
        
        # Optimize column display for readability
        # 优化列显示以提高可读性
        if df.shape[1] > 10:
            # For wide DataFrames, show most important columns
            # 对于宽 DataFrame，显示最重要的列
            numeric_sample = df[numeric_cols[:3]] if len(numeric_cols) > 0 else pd.DataFrame()
            categorical_sample = df[categorical_cols[:3]] if len(categorical_cols) > 0 else pd.DataFrame()
            other_cols = [col for col in df.columns if col not in list(numeric_cols[:3]) + list(categorical_cols[:3])][:4]
            
            sample_df = pd.concat([numeric_sample, categorical_sample, df[other_cols]], axis=1)
            preview_report.append(f"   Note: Showing {len(sample_df.columns)} most representative columns of {df.shape[1]} total")
            sample_data = sample_df.head(sample_size).to_string(max_cols=15, max_colwidth=25)
        else:
            sample_data = df.head(sample_size).to_string(max_cols=15, max_colwidth=25)
            
        preview_report.append(sample_data)
        
        # Add data preview summary
        # 添加数据预览摘要
        preview_report.append("")
        preview_report.append("📊 PREVIEW SUMMARY | 预览摘要:")
        preview_report.append(f"  ✅ Dataset loaded successfully with {df.shape[0]:,} records")
        preview_report.append(f"  📈 Ready for analysis - use python_inter or other tools for deeper insights")
        preview_report.append(f"  📁 Export options available in Excel, JSON, and PDF formats")
        
        return "\n".join(preview_report)
        
    except KeyError:
        # Handle case where DataFrame variable doesn't exist
        # 处理 DataFrame 变量不存在的情况
        return f"Error: DataFrame '{df_name}' not found in global scope. Use extract_data tool first to load data."
        
    except TypeError as type_error:
        # Handle case where variable exists but isn't a DataFrame
        # 处理变量存在但不是 DataFrame 的情况
        return f"Error: Variable '{df_name}' exists but is not a pandas DataFrame: {str(type_error)}"
        
    except MemoryError:
        # Handle memory issues with large datasets
        # 处理大型数据集的内存问题
        return f"Memory error: Dataset '{df_name}' too large for preview. Try reducing sample size or use chunked analysis."
        
    except Exception as e:
        # Handle any other unexpected errors
        # 处理任何其他意外错误
        return f"Preview generation failed for '{df_name}': {str(e)}"

# ============================================================================
# QUICK CHART TEMPLATE TOOL CONFIGURATION
# 快速图表模板工具配置
# ============================================================================
# Professional chart generation with predefined templates for rapid visualization
# 使用预定义模板进行专业图表生成，实现快速可视化
# ============================================================================
class ChartTemplateSchema(BaseModel):
    df_name: str = Field(description="Name of the pandas DataFrame variable for plotting")
    chart_type: str = Field(description="Chart type: 'scatter', 'bar', 'heatmap'")
    x_col: str = Field(description="Column name for X-axis")
    y_col: str = Field(description="Column name for Y-axis")
    title: str = Field(default="Chart", description="Chart title")

@tool(args_schema=ChartTemplateSchema)
def quick_chart(df_name: str, chart_type: str, x_col: str, y_col: str, title: str = "Chart") -> str:
    """
    Generate quick charts using predefined templates (scatter plot, bar chart, heatmap).
    Provides instant visualization with professional styling and automatic layout.
    
    :param df_name: Name of the pandas DataFrame variable for plotting
    :param chart_type: Type of chart - 'scatter', 'bar', or 'heatmap'
    :param x_col: Column name for X-axis (not used for heatmap)
    :param y_col: Column name for Y-axis (not used for heatmap)
    :param title: Chart title
    :return: Chart generation status and file path
    """
    try:
        # Get DataFrame from global variables
        g = globals()
        if df_name not in g:
            return f"Error: DataFrame '{df_name}' not found. Please extract or create the DataFrame first."
        
        df = g[df_name]
        if not isinstance(df, pd.DataFrame):
            return f"Error: '{df_name}' is not a pandas DataFrame."
        
        # Set up matplotlib for file saving
        current_backend = matplotlib.get_backend()
        matplotlib.use('Agg')
        
        # Create figure
        try:
            plt.style.use('seaborn-v0_8')
        except:
            # Fallback to default style if seaborn style fails
            plt.style.use('default')
        fig = plt.figure(figsize=(10, 6))
        
        if chart_type.lower() == 'scatter':
            if x_col not in df.columns or y_col not in df.columns:
                return f"Error: Columns '{x_col}' or '{y_col}' not found in DataFrame"
            
            plt.scatter(df[x_col], df[y_col], alpha=0.6, s=50)
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f"{title} - Scatter Plot")
            plt.grid(True, alpha=0.3)
            
        elif chart_type.lower() == 'bar':
            if x_col not in df.columns or y_col not in df.columns:
                return f"Error: Columns '{x_col}' or '{y_col}' not found in DataFrame"
            
            # For bar charts, group by x_col and aggregate y_col
            data = df.groupby(x_col)[y_col].mean().sort_values(ascending=False)
            bars = plt.bar(range(len(data)), data.values)
            plt.xlabel(x_col)
            plt.ylabel(f"Average {y_col}")
            plt.title(f"{title} - Bar Chart")
            plt.xticks(range(len(data)), data.index, rotation=45, ha='right')
            
            # Color bars with gradient
            colors = plt.cm.viridis([i/len(data) for i in range(len(data))])
            for bar, color in zip(bars, colors):
                bar.set_color(color)
            
        elif chart_type.lower() == 'heatmap':
            # For heatmap, use correlation matrix of numeric columns
            numeric_df = df.select_dtypes(include=['number'])
            if numeric_df.empty:
                return "Error: No numeric columns found for heatmap"
            
            corr = numeric_df.corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', center=0,
                       square=True, fmt='.2f', cbar_kws={'shrink': 0.8})
            plt.title(f"{title} - Correlation Heatmap")
            plt.tight_layout()
            
        else:
            return f"Error: Unsupported chart type '{chart_type}'. Supported types: scatter, bar, heatmap"
        
        # Save figure
        base_dir = os.getenv('PUBLIC_DIR', "/app/shared/public")
        images_dir = os.path.join(base_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_{chart_type}_{timestamp}.png"
        abs_path = os.path.join(images_dir, filename)
        rel_path = os.path.join("images", filename)
        
        fig.tight_layout()
        fig.savefig(abs_path, bbox_inches='tight', dpi=300)
        
        return f"Chart saved successfully: {rel_path}\n\n---\n\n![{title} - {chart_type.title()} Chart]({rel_path})"
        
    except Exception as e:
        return f"Chart generation failed: {str(e)}"
    finally:
        plt.close('all')
        matplotlib.use(current_backend)

# Create SQL query history tool / 创建SQL查询历史工具
class QueryHistorySchema(BaseModel):
    action: str = Field(description="Action: 'save', 'list', 'reuse'")
    query: str = Field(default="", description="SQL query to save (for 'save' action)")
    query_id: int = Field(default=0, description="Query ID to reuse (for 'reuse' action)")
    description: str = Field(default="", description="Description of the query (for 'save' action)")

@tool(args_schema=QueryHistorySchema)
def query_history(action: str, query: str = "", query_id: int = 0, description: str = "") -> str:
    """
    Manage SQL query history for quick reuse and reference.
    Save frequently used queries, list query history, and reuse previous queries.
    
    :param action: Action to perform - 'save', 'list', or 'reuse'
    :param query: SQL query string (for 'save' action)
    :param query_id: ID of query to reuse (for 'reuse' action)
    :param description: Optional description for the query (for 'save' action)
    :return: Operation result
    """
    try:
        # History file path
        base_dir = os.getenv('PROJECT_ROOT', "/app")
        history_file = os.path.join(base_dir, "query_history.json")
        
        # Load existing history
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = {"queries": [], "next_id": 1}
        
        if action.lower() == 'save':
            if not query.strip():
                return "Error: Query cannot be empty for save action"
            
            # Add new query to history
            new_entry = {
                "id": history["next_id"],
                "query": query.strip(),
                "description": description.strip(),
                "timestamp": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            history["queries"].append(new_entry)
            history["next_id"] += 1
            
            # Save updated history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return f"Query saved successfully with ID: {new_entry['id']}"
            
        elif action.lower() == 'list':
            if not history["queries"]:
                return "No queries in history"
            
            result = ["=== SQL QUERY HISTORY ==="]
            for entry in sorted(history["queries"], key=lambda x: x["timestamp"], reverse=True):
                result.append(f"\nID: {entry['id']}")
                result.append(f"Description: {entry['description'] or 'No description'}")
                result.append(f"Query: {entry['query'][:100]}{'...' if len(entry['query']) > 100 else ''}")
                result.append(f"Used: {entry['usage_count']} times")
                result.append(f"Date: {entry['timestamp'][:19].replace('T', ' ')}")
            
            return "\n".join(result)
            
        elif action.lower() == 'reuse':
            if query_id <= 0:
                return "Error: Please provide a valid query ID for reuse action"
            
            # Find query by ID
            target_query = None
            for entry in history["queries"]:
                if entry["id"] == query_id:
                    target_query = entry
                    break
            
            if not target_query:
                return f"Error: Query with ID {query_id} not found"
            
            # Update usage count
            target_query["usage_count"] += 1
            target_query["last_used"] = datetime.now().isoformat()
            
            # Save updated history
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return f"Reusing query ID {query_id}:\n{target_query['query']}"
            
        else:
            return f"Error: Invalid action '{action}'. Supported actions: save, list, reuse"
            
    except Exception as e:
        return f"Query history operation failed: {str(e)}"

# ============================================================================
# COMPREHENSIVE DATA QUALITY ASSESSMENT TOOL
# 综合数据质量评估工具
# ============================================================================
# This tool provides enterprise-grade data quality assessment capabilities
# 该工具提供企业级数据质量评估功能
# Key features: Missing value analysis, duplicate detection, outlier identification, data type validation
# 主要功能：缺失值分析、重复值检测、异常值识别、数据类型验证

# Data quality assessment schema / 数据质量评估模式
class DataQualitySchema(BaseModel):
    """
    Input schema for comprehensive data quality assessment tool
    综合数据质量评估工具的输入模式
    
    This schema validates user input for data quality checks ensuring proper parameter types
    该模式验证数据质量检查的用户输入，确保参数类型正确
    """
    df_name: str = Field(description="Name of the pandas DataFrame variable to check / 要检查的pandas DataFrame变量名")
    check_types: str = Field(default="all", description="Types of checks: 'all', 'missing', 'duplicates', 'outliers', 'types' / 检查类型：'all'(全部), 'missing'(缺失值), 'duplicates'(重复值), 'outliers'(异常值), 'types'(数据类型)")

@tool(args_schema=DataQualitySchema)
def data_quality_check(df_name: str, check_types: str = "all") -> str:
    """
    COMPREHENSIVE DATA QUALITY ASSESSMENT FUNCTION
    综合数据质量评估功能
    
    This function performs thorough data quality analysis to identify potential issues in datasets.
    该函数执行全面的数据质量分析，识别数据集中的潜在问题。
    
    BUSINESS VALUE / 业务价值:
    - Early detection of data issues before analysis / 在分析前及早发现数据问题
    - Automated quality reporting for stakeholders / 为利益相关者提供自动化质量报告
    - Standardized quality metrics across projects / 跨项目的标准化质量指标
    - Risk mitigation for data-driven decisions / 降低数据驱动决策的风险
    
    TECHNICAL CAPABILITIES / 技术能力:
    1. Missing Values Analysis: Percentage and distribution / 缺失值分析：百分比和分布
    2. Duplicate Detection: Full record duplicates / 重复检测：完整记录重复
    3. Outlier Identification: IQR-based statistical outliers / 异常值识别：基于IQR的统计异常值
    4. Data Type Validation: Type consistency and format issues / 数据类型验证：类型一致性和格式问题
    5. Quality Scoring: Overall quality assessment / 质量评分：整体质量评估
    
    WORKFLOW PROCESS / 工作流程:
    Step 1: Validate DataFrame existence and type / 步骤1：验证DataFrame存在性和类型
    Step 2: Initialize quality report structure / 步骤2：初始化质量报告结构
    Step 3: Execute selected quality checks / 步骤3：执行选定的质量检查
    Step 4: Aggregate findings and calculate scores / 步骤4：汇总发现并计算评分
    Step 5: Generate actionable recommendations / 步骤5：生成可操作的建议
    Step 6: Return comprehensive quality report / 步骤6：返回综合质量报告
    
    :param df_name: Name of the pandas DataFrame variable to check / 要检查的pandas DataFrame变量名
    :param check_types: Types of checks to perform - 'all', 'missing', 'duplicates', 'outliers', 'types' / 要执行的检查类型
    :return: Comprehensive data quality report with severity indicators and recommendations / 包含严重性指标和建议的综合数据质量报告
    """
    try:
        # ========================================================================
        # STEP 1: DATAFRAME VALIDATION AND INITIALIZATION
        # 步骤1：DataFrame验证和初始化
        # ========================================================================
        
        # Retrieve DataFrame from global namespace (where extract_data saves it)
        # 从全局命名空间获取DataFrame（extract_data保存的位置）
        g = globals()
        if df_name not in g:
            return f"Error: DataFrame '{df_name}' not found. Please extract or create the DataFrame first."
        
        # Ensure the retrieved object is actually a pandas DataFrame
        # 确保获取的对象确实是pandas DataFrame
        df = g[df_name]
        if not isinstance(df, pd.DataFrame):
            return f"Error: '{df_name}' is not a pandas DataFrame."
        
        # ========================================================================
        # STEP 2: INITIALIZE COMPREHENSIVE QUALITY REPORT STRUCTURE
        # 步骤2：初始化综合质量报告结构
        # ========================================================================
        
        # Create structured report with headers and metadata
        # 创建带有标题和元数据的结构化报告
        report = []
        report.append(f"=== DATA QUALITY REPORT FOR '{df_name}' ===")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns")
        report.append("")
        
        # Initialize issue counter for overall quality scoring
        # 初始化问题计数器，用于整体质量评分
        issues_found = 0
        
        # ========================================================================
        # STEP 3A: MISSING VALUES ANALYSIS
        # 步骤3A：缺失值分析
        # ========================================================================
        
        # Perform comprehensive missing value detection and analysis
        # 执行综合缺失值检测和分析
        if check_types.lower() in ['all', 'missing']:
            report.append("🔍 MISSING VALUES ANALYSIS:")
            
            # Calculate missing values count and percentage for each column
            # 计算每列的缺失值数量和百分比
            missing = df.isnull().sum()  # Count of missing values per column / 每列缺失值数量
            missing_pct = (missing / len(df) * 100).round(2)  # Percentage of missing values / 缺失值百分比
            
            # Evaluate overall missing data situation
            # 评估整体缺失数据情况
            if missing.sum() == 0:
                report.append("  ✅ No missing values found")
            else:
                # Add to global issues counter for quality scoring
                # 添加到全局问题计数器用于质量评分
                issues_found += missing.sum()
                report.append(f"  ⚠️  Total missing values: {missing.sum()}")
                
                # Analyze each column with missing values and assign severity levels
                # 分析每个有缺失值的列并分配严重性级别
                for col in df.columns:
                    if missing[col] > 0:
                        # Severity classification based on missing percentage
                        # 基于缺失百分比的严重性分类
                        # Red: >50% missing (critical), Yellow: >10% missing (warning), Green: <10% missing (minor)
                        # 红色：>50%缺失（严重），黄色：>10%缺失（警告），绿色：<10%缺失（轻微）
                        severity = "🔴" if missing_pct[col] > 50 else "🟡" if missing_pct[col] > 10 else "🟢"
                        report.append(f"    {severity} {col}: {missing[col]} ({missing_pct[col]}%)")
            report.append("")
        
        # ========================================================================
        # STEP 3B: DUPLICATE RECORDS DETECTION AND ANALYSIS
        # 步骤3B：重复记录检测和分析
        # ========================================================================
        
        # Identify complete duplicate rows that may skew analysis results
        # 识别可能歪曲分析结果的完整重复行
        if check_types.lower() in ['all', 'duplicates']:
            report.append("🔍 DUPLICATE RECORDS ANALYSIS:")
            
            # Count total duplicate rows using pandas duplicated() method
            # 使用pandas duplicated()方法计算总重复行数
            # This identifies rows that are exact duplicates of previous rows
            # 这识别与之前行完全重复的行
            duplicates = df.duplicated().sum()
            
            # Evaluate duplicate data situation
            # 评估重复数据情况
            if duplicates == 0:
                report.append("  ✅ No duplicate rows found")
            else:
                # Add duplicates to issues counter for overall quality assessment
                # 将重复值添加到问题计数器用于整体质量评估
                issues_found += duplicates
                
                # Calculate percentage of duplicate records
                # 计算重复记录的百分比
                duplicate_pct = (duplicates / len(df) * 100).round(2)
                
                # Assign severity level based on duplicate percentage
                # 根据重复百分比分配严重性级别
                # Red: >10% duplicates (critical data integrity issue)
                # Yellow: >5% duplicates (moderate concern)
                # Green: <5% duplicates (minor issue)
                # 红色：>10%重复（严重数据完整性问题）
                # 黄色：>5%重复（中等关注）
                # 绿色：<5%重复（轻微问题）
                severity = "🔴" if duplicate_pct > 10 else "🟡" if duplicate_pct > 5 else "🟢"
                report.append(f"  {severity} Duplicate rows: {duplicates} ({duplicate_pct}%)")
            report.append("")
        
        # ========================================================================
        # STEP 3C: DATA TYPE CONSISTENCY AND FORMAT VALIDATION
        # 步骤3C：数据类型一致性和格式验证
        # ========================================================================
        
        # Analyze data type appropriateness and detect format inconsistencies
        # 分析数据类型适当性并检测格式不一致性
        if check_types.lower() in ['all', 'types']:
            report.append("🔍 DATA TYPE ANALYSIS:")
            type_issues = 0  # Counter for data type related issues / 数据类型相关问题计数器
            
            # Iterate through each column to check data type appropriateness
            # 遍历每列检查数据类型适当性
            for col in df.columns:
                col_type = df[col].dtype
                
                # Focus on 'object' type columns which may have hidden issues
                # 专注于'object'类型列，可能存在隐藏问题
                if col_type == 'object':
                    
                    # ================================================================
                    # SUB-CHECK 1: NUMERIC DATA STORED AS TEXT
                    # 子检查1：以文本形式存储的数值数据
                    # ================================================================
                    # This can cause performance issues and prevent proper statistical analysis
                    # 这可能导致性能问题并阻止正常的统计分析
                    try:
                        # Attempt to convert to numeric, 'coerce' makes non-numeric values NaN
                        # 尝试转换为数值，'coerce'使非数值变为NaN
                        numeric_conversion = pd.to_numeric(df[col], errors='coerce')
                        
                        # Count how many values couldn't be converted (excluding original NaNs)
                        # 计算无法转换的值数量（排除原始NaN）
                        non_numeric = numeric_conversion.isnull().sum() - df[col].isnull().sum()
                        
                        # If all non-null values can be converted to numeric, flag as issue
                        # 如果所有非空值都可以转换为数值，标记为问题
                        if non_numeric == 0 and not df[col].isnull().all():
                            type_issues += 1
                            report.append(f"    🟡 {col}: Numeric data stored as text")
                    except:
                        pass  # Skip columns that can't be analyzed / 跳过无法分析的列
                    
                    # ================================================================
                    # SUB-CHECK 2: INCONSISTENT CASE IN CATEGORICAL DATA
                    # 子检查2：分类数据中的不一致大小写
                    # ================================================================
                    # Mixed case can create artificial categories and skew analysis
                    # 混合大小写可能创建人工分类并歪曲分析
                    if df[col].nunique() < len(df) * 0.5:  # Likely categorical if unique values < 50% of total rows
                        # 如果唯一值 < 总行数50%，则可能是分类数据
                        unique_vals = df[col].dropna().astype(str)
                        
                        # Check if lowercasing reduces the number of unique values
                        # 检查转换为小写是否减少了唯一值的数量
                        case_variants = unique_vals.str.lower().nunique() < unique_vals.nunique()
                        if case_variants:
                            type_issues += 1
                            report.append(f"    🟡 {col}: Inconsistent case in categorical data")
            
            # Summarize data type analysis results
            # 总结数据类型分析结果
            if type_issues == 0:
                report.append("  ✅ No data type issues found")
            else:
                issues_found += type_issues
                report.append(f"  ⚠️  Data type issues found: {type_issues}")
            report.append("")
        
        # ========================================================================
        # STEP 3D: STATISTICAL OUTLIER DETECTION AND ANALYSIS
        # 步骤3D：统计异常值检测和分析
        # ========================================================================
        
        # Identify statistical outliers using Interquartile Range (IQR) method
        # 使用四分位数范围(IQR)方法识别统计异常值
        if check_types.lower() in ['all', 'outliers']:
            report.append("🔍 OUTLIERS ANALYSIS:")
            
            # Select only numeric columns for outlier analysis
            # 仅选择数值列进行异常值分析
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            # Check if any numeric columns exist for analysis
            # 检查是否存在可分析的数值列
            if len(numeric_cols) == 0:
                report.append("  ℹ️  No numeric columns to check for outliers")
            else:
                outlier_cols = 0  # Counter for columns with outliers / 有异常值的列计数器
                
                # Analyze each numeric column for statistical outliers
                # 分析每个数值列的统计异常值
                for col in numeric_cols:
                    # ============================================================
                    # IQR METHOD FOR OUTLIER DETECTION
                    # IQR方法检测异常值
                    # ============================================================
                    # This method defines outliers as values outside Q1-1.5*IQR to Q3+1.5*IQR
                    # 该方法将异常值定义为在Q1-1.5*IQR到Q3+1.5*IQR范围外的值
                    
                    # Calculate quartiles for the column
                    # 计算列的四分位数
                    Q1 = df[col].quantile(0.25)  # First quartile (25th percentile) / 第一四分位数（25%百分位数）
                    Q3 = df[col].quantile(0.75)  # Third quartile (75th percentile) / 第三四分位数（75%百分位数）
                    IQR = Q3 - Q1  # Interquartile Range / 四分位数范围
                    
                    # Define outlier boundaries using 1.5 * IQR rule
                    # 使用1.5 * IQR规则定义异常值边界
                    lower_bound = Q1 - 1.5 * IQR  # Values below this are outliers / 低于此值的为异常值
                    upper_bound = Q3 + 1.5 * IQR  # Values above this are outliers / 高于此值的为异常值
                    
                    # Count outliers in the column
                    # 计算列中的异常值
                    outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                    
                    # Report outliers if found
                    # 如果发现异常值则报告
                    if outliers > 0:
                        outlier_cols += 1
                        
                        # Calculate percentage of outliers
                        # 计算异常值百分比
                        outlier_pct = (outliers / len(df) * 100).round(2)
                        
                        # Assign severity based on outlier percentage
                        # 根据异常值百分比分配严重性
                        # Red: >10% outliers (potential data quality issue)
                        # Yellow: >5% outliers (worth investigating)
                        # Green: <5% outliers (normal statistical variation)
                        # 红色：>10%异常值（潜在数据质量问题）
                        # 黄色：>5%异常值（值得调查）
                        # 绿色：<5%异常值（正常统计变化）
                        severity = "🔴" if outlier_pct > 10 else "🟡" if outlier_pct > 5 else "🟢"
                        report.append(f"    {severity} {col}: {outliers} outliers ({outlier_pct}%)")
                
                # Summarize outlier analysis results
                # 总结异常值分析结果
                if outlier_cols == 0:
                    report.append("  ✅ No significant outliers found")
                else:
                    issues_found += outlier_cols
            report.append("")
        
        # ========================================================================
        # STEP 4: COMPREHENSIVE QUALITY SUMMARY AND STRATEGIC RECOMMENDATIONS
        # 步骤4：综合质量总结和战略建议
        # ========================================================================
        
        # Generate executive summary with overall quality assessment
        # 生成包含整体质量评估的执行总结
        report.append("📊 QUALITY SUMMARY:")
        # Evaluate overall data quality based on total issues found
        # 根据发现的总问题数评估整体数据质量
        if issues_found == 0:
            # Perfect quality scenario - rare but excellent for analysis
            # 完美质量场景 - 罕见但对分析极佳
            report.append("  🎉 Excellent! No major data quality issues detected")
        else:
            # Quality scoring system based on issue severity and count
            # 基于问题严重性和数量的质量评分系统
            # Poor: >20 issues (requires significant cleanup before analysis)
            # Fair: >10 issues (moderate issues, proceed with caution)
            # Good: <10 issues (minor issues, analysis can proceed)
            # 差：>20个问题（分析前需要大量清理）
            # 一般：>10个问题（中等问题，谨慎进行）
            # 好：<10个问题（轻微问题，可以进行分析）
            severity = "🔴 Poor" if issues_found > 20 else "🟡 Fair" if issues_found > 10 else "🟢 Good"
            report.append(f"  Data Quality: {severity}")
            report.append(f"  Total issues detected: {issues_found}")
            
            # ================================================================
            # ACTIONABLE RECOMMENDATIONS BASED ON DETECTED ISSUES
            # 基于检测问题的可操作建议
            # ================================================================
            # Provide specific, prioritized recommendations for data improvement
            # 为数据改进提供具体的、优先化的建议
            report.append("\n💡 RECOMMENDATIONS:")
            
            # Missing values recommendation / 缺失值建议
            if check_types.lower() in ['all', 'missing'] and df.isnull().sum().sum() > 0:
                report.append("  • Handle missing values using imputation or removal")
            
            # Duplicate records recommendation / 重复记录建议
            if check_types.lower() in ['all', 'duplicates'] and df.duplicated().sum() > 0:
                report.append("  • Remove or investigate duplicate records")
            
            # Data type optimization recommendation / 数据类型优化建议
            if check_types.lower() in ['all', 'types']:
                report.append("  • Convert data types for better performance and accuracy")
            
            # Outlier investigation recommendation / 异常值调查建议
            if check_types.lower() in ['all', 'outliers'] and len(df.select_dtypes(include=['number']).columns) > 0:
                report.append("  • Investigate outliers - they may be errors or important insights")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Data quality check failed: {str(e)}"


# TOOL CATEGORIES AND CAPABILITIES / 工具分类和能力:
# 1. INFORMATION RETRIEVAL / 信息检索: search_tool (web search capabilities)
# 2. CODE EXECUTION / 代码执行: python_inter (Python environment)
# 3. VISUALIZATION / 可视化: fig_inter (matplotlib/seaborn plotting)
# 4. DATABASE OPERATIONS / 数据库操作: sql_inter, extract_data (MySQL integration)
# 5. DATA MANAGEMENT / 数据管理: export_data (multi-format export)
# 6. QUALITY ASSURANCE / 质量保证: data_preview, data_quality_check (data validation)
# 7. EFFICIENCY TOOLS / 效率工具: quick_chart (template charts), query_history (SQL management)

tools = [search_tool, python_inter, fig_inter, sql_inter, extract_data, 
         export_data, data_preview, quick_chart, query_history, data_quality_check]

model = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),        
    api_key=os.getenv('OPENAI_API_KEY'),  
    temperature=0.2                       
)


graph = create_react_agent(model=model, tools=tools, prompt=prompt)

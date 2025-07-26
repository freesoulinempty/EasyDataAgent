import os
from dotenv import load_dotenv 
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import matplotlib
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import pymysql
from langchain_tavily import TavilySearch
from datetime import datetime
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

# Wrap as LangGraph tool / 封装为 LangGraph 工具
@tool(args_schema=SQLQuerySchema)
def sql_inter(sql_query: str) -> str:
    """
    Call this function when users need to perform database queries.
    This function runs SQL code on a specified MySQL server for data query tasks,
    using pymysql to connect to the MySQL database.
    This function only handles SQL code execution and data querying. For data extraction, use the extract_data function.
    
    :param sql_query: SQL query statement in string format for querying tables in MySQL database
    :return: Execution result of sql_query in MySQL
    """
    # print("Calling sql_inter tool to run SQL query... / 正在调用 sql_inter 工具运行 SQL 查询...")
    
    # Load environment variables / 加载环境变量
    load_dotenv(override=True)
    host = os.getenv('HOST')
    user = os.getenv('USER')
    mysql_pw = os.getenv('MYSQL_PW')
    db = os.getenv('DB_NAME')
    port = os.getenv('PORT')
    
    # Create connection / 创建连接
    connection = pymysql.connect(
        host=host,
        user=user,
        passwd=mysql_pw,
        db=db,
        port=int(port),
        charset='utf8'
    )
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            # print("SQL query executed successfully, organizing results... / SQL 查询已成功执行，正在整理结果...")
    finally:
        connection.close()

    # Return results as JSON string / 将结果以 JSON 字符串形式返回
    return json.dumps(results, ensure_ascii=False)

# Create data extraction tool / 创建数据提取工具
# Define structured parameters / 定义结构化参数
class ExtractQuerySchema(BaseModel):
    sql_query: str = Field(description="SQL query statement for extracting data from MySQL.")
    df_name: str = Field(description="Specify the pandas variable name for saving results (in string format).")

# Register as Agent tool / 注册为 Agent 工具
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
    print("Calling extract_data tool to run SQL query... / 正在调用 extract_data 工具运行 SQL 查询...")
    
    load_dotenv(override=True)
    host = os.getenv('HOST')
    user = os.getenv('USER')
    mysql_pw = os.getenv('MYSQL_PW')
    db = os.getenv('DB_NAME')
    port = os.getenv('PORT')

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
            # print("代码已顺利执行，正在进行结果梳理...")
            return str(result)
        else:
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
    # print("Calling fig_inter tool to run Python code... / 正在调用fig_inter工具运行Python代码...")

    current_backend = matplotlib.get_backend()
    matplotlib.use('Agg')

    local_vars = {"plt": plt, "pd": pd, "sns": sns}
    
    # Set image save path (your absolute path) / 设置图像保存路径（你自己的绝对路径）
    base_dir = r"/Users/gufang/Documents/GitHub/EasyDataAgent/agent-chat-ui-main/public"
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
            return f"Image saved successfully, path: {rel_path}"
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

# Create data export tool / 创建数据导出工具
class DataExportSchema(BaseModel):
    df_name: str = Field(description="Name of the pandas DataFrame variable to export")
    format_type: str = Field(description="Export format: 'excel', 'json', or 'pdf'")
    filename: str = Field(description="Output filename (without extension)")

@tool(args_schema=DataExportSchema)
def export_data(df_name: str, format_type: str, filename: str) -> str:
    """
    Export pandas DataFrame to various formats (Excel, JSON, PDF).
    Supports exporting analysis results to different file formats for sharing and reporting.
    
    :param df_name: Name of the pandas DataFrame variable to export
    :param format_type: Export format - 'excel', 'json', or 'pdf'
    :param filename: Output filename without extension
    :return: Export status and file path
    """
    try:
        # Get DataFrame from global variables
        g = globals()
        if df_name not in g:
            return f"Error: DataFrame '{df_name}' not found. Please extract or create the DataFrame first."
        
        df = g[df_name]
        if not isinstance(df, pd.DataFrame):
            return f"Error: '{df_name}' is not a pandas DataFrame."
        
        # Set base directory for exports
        base_dir = r"/Users/gufang/Documents/GitHub/EasyDataAgent/agent-chat-ui-main/public"
        exports_dir = os.path.join(base_dir, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        
        if format_type.lower() == 'excel':
            file_path = os.path.join(exports_dir, f"{filename}.xlsx")
            df.to_excel(file_path, index=True, engine='openpyxl')
            rel_path = os.path.join("exports", f"{filename}.xlsx")
            return f"Excel file exported successfully: {rel_path}"
            
        elif format_type.lower() == 'json':
            file_path = os.path.join(exports_dir, f"{filename}.json")
            df.to_json(file_path, orient='records', date_format='iso', indent=2)
            rel_path = os.path.join("exports", f"{filename}.json")
            return f"JSON file exported successfully: {rel_path}"
            
        elif format_type.lower() == 'pdf':
            file_path = os.path.join(exports_dir, f"{filename}.pdf")
            
            # Create PDF document
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Add title
            title = Paragraph(f"Data Export: {df_name}", styles['Title'])
            elements.append(title)
            
            # Add timestamp
            timestamp = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
            elements.append(timestamp)
            
            # Convert DataFrame to table data (limit rows for PDF)
            data = [df.columns.tolist()]
            max_rows = min(50, len(df))  # Limit to 50 rows for PDF
            for _, row in df.head(max_rows).iterrows():
                data.append([str(x) for x in row.tolist()])
            
            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            if len(df) > max_rows:
                note = Paragraph(f"Note: Only first {max_rows} rows shown. Total rows: {len(df)}", styles['Normal'])
                elements.append(note)
            
            doc.build(elements)
            rel_path = os.path.join("exports", f"{filename}.pdf")
            return f"PDF file exported successfully: {rel_path}"
            
        else:
            return f"Error: Unsupported format '{format_type}'. Supported formats: excel, json, pdf"
            
    except Exception as e:
        return f"Export failed: {str(e)}"

# Create data preview tool / 创建数据预览工具
class DataPreviewSchema(BaseModel):
    df_name: str = Field(description="Name of the pandas DataFrame variable to preview")
    rows: int = Field(default=10, description="Number of rows to display (default: 10)")

@tool(args_schema=DataPreviewSchema)
def data_preview(df_name: str, rows: int = 10) -> str:
    """
    Generate a comprehensive data preview snapshot including basic info, data types, missing values, and sample data.
    Perfect for quick data exploration and quality assessment.
    
    :param df_name: Name of the pandas DataFrame variable to preview
    :param rows: Number of sample rows to display (default: 10)
    :return: Comprehensive data preview report
    """
    try:
        # Get DataFrame from global variables
        g = globals()
        if df_name not in g:
            return f"Error: DataFrame '{df_name}' not found. Please extract or create the DataFrame first."
        
        df = g[df_name]
        if not isinstance(df, pd.DataFrame):
            return f"Error: '{df_name}' is not a pandas DataFrame."
        
        # Generate comprehensive preview
        preview_report = []
        preview_report.append(f"=== DATA PREVIEW SNAPSHOT FOR '{df_name}' ===")
        preview_report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        preview_report.append("")
        
        # Basic information
        preview_report.append("📊 BASIC INFORMATION:")
        preview_report.append(f"  • Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        preview_report.append(f"  • Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        preview_report.append(f"  • Index type: {type(df.index).__name__}")
        preview_report.append("")
        
        # Data types
        preview_report.append("🏷️  DATA TYPES:")
        for col, dtype in df.dtypes.items():
            preview_report.append(f"  • {col}: {dtype}")
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
        
        # Sample data
        preview_report.append(f"📋 SAMPLE DATA (first {min(rows, len(df))} rows):")
        sample_data = df.head(rows).to_string(max_cols=10, max_colwidth=20)
        preview_report.append(sample_data)
        
        return "\n".join(preview_report)
        
    except Exception as e:
        return f"Preview generation failed: {str(e)}"

# Create chart templates tool / 创建图表模板工具
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
        base_dir = r"/Users/gufang/Documents/GitHub/EasyDataAgent/agent-chat-ui-main/public"
        images_dir = os.path.join(base_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quick_{chart_type}_{timestamp}.png"
        abs_path = os.path.join(images_dir, filename)
        rel_path = os.path.join("images", filename)
        
        fig.tight_layout()
        fig.savefig(abs_path, bbox_inches='tight', dpi=300)
        
        return f"Chart saved successfully: {rel_path}"
        
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
        base_dir = r"/Users/gufang/Documents/GitHub/EasyDataAgent"
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

# Create data quality check tool / 创建数据质量检查工具
class DataQualitySchema(BaseModel):
    df_name: str = Field(description="Name of the pandas DataFrame variable to check")
    check_types: str = Field(default="all", description="Types of checks: 'all', 'missing', 'duplicates', 'outliers', 'types'")

@tool(args_schema=DataQualitySchema)
def data_quality_check(df_name: str, check_types: str = "all") -> str:
    """
    Comprehensive data quality assessment including missing values, duplicates, outliers, and data type issues.
    Generates detailed quality report with actionable insights.
    
    :param df_name: Name of the pandas DataFrame variable to check
    :param check_types: Types of checks to perform - 'all', 'missing', 'duplicates', 'outliers', 'types'
    :return: Comprehensive data quality report
    """
    try:
        # Get DataFrame from global variables
        g = globals()
        if df_name not in g:
            return f"Error: DataFrame '{df_name}' not found. Please extract or create the DataFrame first."
        
        df = g[df_name]
        if not isinstance(df, pd.DataFrame):
            return f"Error: '{df_name}' is not a pandas DataFrame."
        
        report = []
        report.append(f"=== DATA QUALITY REPORT FOR '{df_name}' ===")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Dataset: {df.shape[0]} rows × {df.shape[1]} columns")
        report.append("")
        
        issues_found = 0
        
        # Check missing values
        if check_types.lower() in ['all', 'missing']:
            report.append("🔍 MISSING VALUES ANALYSIS:")
            missing = df.isnull().sum()
            missing_pct = (missing / len(df) * 100).round(2)
            
            if missing.sum() == 0:
                report.append("  ✅ No missing values found")
            else:
                issues_found += missing.sum()
                report.append(f"  ⚠️  Total missing values: {missing.sum()}")
                for col in df.columns:
                    if missing[col] > 0:
                        severity = "🔴" if missing_pct[col] > 50 else "🟡" if missing_pct[col] > 10 else "🟢"
                        report.append(f"    {severity} {col}: {missing[col]} ({missing_pct[col]}%)")
            report.append("")
        
        # Check duplicates
        if check_types.lower() in ['all', 'duplicates']:
            report.append("🔍 DUPLICATE RECORDS ANALYSIS:")
            duplicates = df.duplicated().sum()
            if duplicates == 0:
                report.append("  ✅ No duplicate rows found")
            else:
                issues_found += duplicates
                duplicate_pct = (duplicates / len(df) * 100).round(2)
                severity = "🔴" if duplicate_pct > 10 else "🟡" if duplicate_pct > 5 else "🟢"
                report.append(f"  {severity} Duplicate rows: {duplicates} ({duplicate_pct}%)")
            report.append("")
        
        # Check data types and format issues
        if check_types.lower() in ['all', 'types']:
            report.append("🔍 DATA TYPE ANALYSIS:")
            type_issues = 0
            
            for col in df.columns:
                col_type = df[col].dtype
                if col_type == 'object':
                    # Check if numeric data is stored as string
                    try:
                        numeric_conversion = pd.to_numeric(df[col], errors='coerce')
                        non_numeric = numeric_conversion.isnull().sum() - df[col].isnull().sum()
                        if non_numeric == 0 and not df[col].isnull().all():
                            type_issues += 1
                            report.append(f"    🟡 {col}: Numeric data stored as text")
                    except:
                        pass
                    
                    # Check for mixed case in categorical data
                    if df[col].nunique() < len(df) * 0.5:  # Likely categorical
                        unique_vals = df[col].dropna().astype(str)
                        case_variants = unique_vals.str.lower().nunique() < unique_vals.nunique()
                        if case_variants:
                            type_issues += 1
                            report.append(f"    🟡 {col}: Inconsistent case in categorical data")
            
            if type_issues == 0:
                report.append("  ✅ No data type issues found")
            else:
                issues_found += type_issues
                report.append(f"  ⚠️  Data type issues found: {type_issues}")
            report.append("")
        
        # Check outliers in numeric columns
        if check_types.lower() in ['all', 'outliers']:
            report.append("🔍 OUTLIERS ANALYSIS:")
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            if len(numeric_cols) == 0:
                report.append("  ℹ️  No numeric columns to check for outliers")
            else:
                outlier_cols = 0
                for col in numeric_cols:
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                    if outliers > 0:
                        outlier_cols += 1
                        outlier_pct = (outliers / len(df) * 100).round(2)
                        severity = "🔴" if outlier_pct > 10 else "🟡" if outlier_pct > 5 else "🟢"
                        report.append(f"    {severity} {col}: {outliers} outliers ({outlier_pct}%)")
                
                if outlier_cols == 0:
                    report.append("  ✅ No significant outliers found")
                else:
                    issues_found += outlier_cols
            report.append("")
        
        # Summary
        report.append("📊 QUALITY SUMMARY:")
        if issues_found == 0:
            report.append("  🎉 Excellent! No major data quality issues detected")
        else:
            severity = "🔴 Poor" if issues_found > 20 else "🟡 Fair" if issues_found > 10 else "🟢 Good"
            report.append(f"  Data Quality: {severity}")
            report.append(f"  Total issues detected: {issues_found}")
            report.append("\n💡 RECOMMENDATIONS:")
            if check_types.lower() in ['all', 'missing'] and df.isnull().sum().sum() > 0:
                report.append("  • Handle missing values using imputation or removal")
            if check_types.lower() in ['all', 'duplicates'] and df.duplicated().sum() > 0:
                report.append("  • Remove or investigate duplicate records")
            if check_types.lower() in ['all', 'types']:
                report.append("  • Convert data types for better performance and accuracy")
            if check_types.lower() in ['all', 'outliers'] and len(df.select_dtypes(include=['number']).columns) > 0:
                report.append("  • Investigate outliers - they may be errors or important insights")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"Data quality check failed: {str(e)}"

# Create tool list / 创建工具列表
tools = [search_tool, python_inter, fig_inter, sql_inter, extract_data, 
         export_data, data_preview, quick_chart, query_history, data_quality_check]

# Create model / 创建模型
model = ChatOpenAI(
    model=os.getenv('MODEL_NAME'),
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=0.2
)

# Create graph (Agent) / 创建图 （Agent）
graph = create_react_agent(model=model, tools=tools, prompt=prompt)
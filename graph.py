import os
from dotenv import load_dotenv 
from langchain_deepseek import ChatDeepSeek
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

# Create prompt template / 创建提示词模板
prompt = """
You are an experienced intelligent data analysis assistant, skilled at helping users efficiently complete the following tasks:

1. **Database Queries:**
   - When users need to retrieve data from databases or perform SQL queries, call the `sql_inter` tool. This tool has built-in pymysql connection parameters for MySQL databases, including database name, username, password, port, etc. You only need to generate SQL statements based on user requirements.
   - You need to accurately generate SQL statements based on user requests, such as `SELECT * FROM table_name` or queries with conditions.

2. **Data Table Extraction:**
   - When users want to import database tables into Python environment for subsequent analysis, call the `extract_data` tool.
   - You need to generate SQL query statements based on table names or query conditions provided by users, and save the data to specified pandas variables.

3. **Non-plotting Python Code Execution:**
   - When users need to execute Python scripts or perform data processing and statistical calculations, call the `python_inter` tool.
   - Limited to executing non-plotting code, such as variable definitions, data analysis, etc.

4. **Plotting Python Code Execution:**
   - When users need visualization displays (such as generating charts, plotting distributions), call the `fig_inter` tool.
   - You can directly read data and create plots without using the `python_inter` tool to read images.
   - You should write plotting code based on user requirements and correctly specify the plotting object variable name (such as `fig`).
   - When generating Python plotting code, you must specify the image name, such as fig = plt.figure() or fig = plt.subplots() to create image objects and assign them to fig.
   - Do not call plt.show(), otherwise the image cannot be saved.

5. **Web Search:**
   - When users ask questions unrelated to data analysis (such as latest news, real-time information), call the `search_tool`.

**Tool Usage Priority:**
- If database data is needed, first use `sql_inter` or `extract_data` to obtain it, then execute Python analysis or plotting.
- If plotting is needed, first ensure data is loaded as pandas objects.

**Response Requirements:**
- All responses use **English/Chinese**, clear, polite, and concise, responding in the user's language.
- If tool calls return structured JSON data, extract key information for brief explanation and display main results.
- If more information is needed from users, proactively ask clear questions.
- If generated image files exist, must insert images in Markdown format in responses, such as: ![Categorical Features vs Churn](images/fig.png)
- Do not output only image path text.

**Style:**
- Professional, concise, data-driven.
- Do not fabricate non-existent tools or data.

Please provide precise and efficient assistance to users based on the above principles.
"""

# Create tool list / 创建工具列表
tools = [search_tool, python_inter, fig_inter, sql_inter, extract_data]

# Create model / 创建模型
model = ChatDeepSeek(model="deepseek-chat")

# Create graph (Agent) / 创建图 （Agent）
graph = create_react_agent(model=model, tools=tools, prompt=prompt)
from mcp.server.fastmcp import FastMCP
import pandas as pd
import os

mcp = FastMCP("FinanceServer")
DATA_FILE = "transaction_data.csv"

@mcp.tool()
def get_columns() -> str:
    """Returns the columns and types of the loaded data."""
    if not os.path.exists(DATA_FILE):
        return "No data loaded."
    df = pd.read_csv(DATA_FILE)
    return f"Columns: {df.columns.tolist()} | Sample Types: {df.dtypes.to_dict()}"

@mcp.tool()
def run_analysis(python_code: str) -> str:
    """Executes Pandas code on 'df' and returns 'final_result'."""
    if not os.path.exists(DATA_FILE):
        return "Error: Please upload a file first."
    
    df = pd.read_csv(DATA_FILE)
    # Ensure Date column is actually datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        
    local_vars = {'df': df}
    try:
        # Securely execute the LLM's logic
        exec(python_code, {}, local_vars)
        return str(local_vars.get('final_result', "No 'final_result' variable was defined."))
    except Exception as e:
        return f"Calculation Error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")

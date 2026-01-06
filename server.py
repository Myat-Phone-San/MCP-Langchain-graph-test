from mcp.server.fastmcp import FastMCP
import pandas as pd
import os

# Initialize FastMCP
mcp = FastMCP("FinanceServer")
DATA_FILE = "transaction_data.csv"

@mcp.tool()
def get_data_info() -> str:
    """Returns columns and types of the financial data."""
    if not os.path.exists(DATA_FILE):
        return "Data file not found."
    df = pd.read_csv(DATA_FILE)
    return f"Columns: {df.columns.tolist()}"

@mcp.tool()
def run_analysis(python_code: str) -> str:
    """Executes Pandas code and returns 'final_result'."""
    if not os.path.exists(DATA_FILE):
        return "Error: No data."
    df = pd.read_csv(DATA_FILE)
    local_vars = {'df': df}
    try:
        exec(python_code, {}, local_vars)
        return str(local_vars.get('final_result', "Done"))
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    # show_banner=False is vital for stdio transport
    mcp.run(transport="stdio")

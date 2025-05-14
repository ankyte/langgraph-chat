from typing import Optional
import pandas as pd
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field
import pandas as pd
from fpdf import FPDF


# Sample data
holdings_df = pd.DataFrame({
    'Asset': ['Apple', 'Microsoft', 'Tesla', 'Amazon', 'Google'],
    'Weight (%)': [20, 25, 15, 30, 10],
    'Value ($)': [100000, 125000, 75000, 150000, 50000]
})

# Function to generate PDF
def create_pdf(client_name, holdings_df = holdings_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Portfolio Report - {client_name}", ln=True, align='C')
    pdf.ln(10)

    total_value = holdings_df["Value ($)"].sum()
    pdf.cell(200, 10, txt=f"Total Portfolio Value: ${total_value:,.2f}", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt="Holdings:", ln=True)

    # Table header
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, "Asset", 1)
    pdf.cell(40, 10, "Weight (%)", 1)
    pdf.cell(60, 10, "Value ($)", 1)
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", '', 10)
    for index, row in holdings_df.iterrows():
        pdf.cell(60, 10, row["Asset"], 1)
        pdf.cell(40, 10, f'{row["Weight (%)"]}%', 1)
        pdf.cell(60, 10, f'${row["Value ($)"]:,}', 1)
        pdf.ln()

    pdf.output("report.pdf")


class ReportInput(BaseModel):
    port: str = Field(description="port")


class ReportTool(BaseTool):
    name: str = "report_tool"
    description: str = "when user asks they want to get/download pdf report of there portfolio"
    args_schema: Optional[ArgsSchema] = ReportInput
    return_direct: bool = True

    def _run(
        self, port: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> pd.DataFrame:
        """Use the tool."""
        try:
            create_pdf(port)
        except Exception:
            pass
        return f"{port}"

    async def _arun(
        self, port: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(port, run_manager=run_manager.get_sync())
    

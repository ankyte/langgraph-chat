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
import datetime
from util import state_manager 

def create_pdf(client_name, holdings_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Portfolio Report - {client_name}", ln=True, align='C')
    pdf.ln(10)

    # Table header
    pdf.set_font("Arial", 'B', 10)
    col_width = 190 / len(holdings_df.columns)  # Adjust column width based on number of columns
    for col in holdings_df.columns:
        pdf.cell(col_width, 10, col, 1)
    pdf.ln()

    # Table rows
    pdf.set_font("Arial", '', 10)
    for _, row in holdings_df.iterrows():
        for item in row:
            pdf.cell(col_width, 10, str(item), 1)
        pdf.ln()

    pdf.output("report.pdf")


class ReportInput(BaseModel):
    port: str = Field(description="port")
    report_date: datetime.date


class ReportTool(BaseTool):
    name: str = "report_tool"
    description: str = "when user asks they want to get/download pdf report of their report, strictly dont output any url link to report, user provided port and report date, dataframes are cached with key dependent of port and report_date"
    args_schema: Optional[ArgsSchema] = ReportInput
    return_direct: bool = True

    def _run(
        self, port: str, report_date: datetime.date, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> pd.DataFrame:
        """Use the tool."""
        try:
            data_id = repr({
                'port': port,
                'report_date': str(report_date)
            })
            df = state_manager.get(data_id)
            create_pdf(port, df)
        except Exception as exp:
            print(exp)
        return f"{port}"

    async def _arun(
        self, port: str,
        report_date: datetime.date,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(port, report_date, run_manager=run_manager.get_sync())
    

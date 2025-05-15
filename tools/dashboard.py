from typing import Optional
import pandas as pd
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

class DashboardInput(BaseModel):
    port: str = Field(description="port")

class DashboardTool(BaseTool):
    name: str = "dashboard_tool"
    description: str = "when user ask for dashboard"
    args_schema: Optional[ArgsSchema] = DashboardInput
    return_direct: bool = True

    def _run(
        self, port: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> pd.DataFrame:
        """Use the tool."""
        return f"{port}"

    async def _arun(
        self, port: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(port, run_manager=run_manager.get_sync())
    


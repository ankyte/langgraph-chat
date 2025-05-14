from typing import Optional
import pandas as pd
import datetime
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

class DataInput(BaseModel):
    a: str = Field(description="port")
    b: datetime.date = Field(description="end_date")

class DataFetchTool(BaseTool):
    name: str = "data_fetch_tool"
    description: str = "useful for when you need are asked to fetch dataframe/data for a portfolio"
    args_schema: Optional[ArgsSchema] = DataInput
    return_direct: bool = True

    def _run(
        self, a: str, b: datetime.date, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> pd.DataFrame:
        """Use the tool."""
        df = pd.DataFrame({
            "a": [1,2,3,4,5,6],
            "b": [b + datetime.timedelta(days=i) for i in range(6)]
        })
        
        return df

    async def _arun(
        self,
        a: str,
        b: datetime.date,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(a, b, run_manager=run_manager.get_sync())
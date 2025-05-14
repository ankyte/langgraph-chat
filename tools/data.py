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
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from util import state_manager
from .mocked_data import get_trades_data

class DataInput(BaseModel):
    port: str = Field(description="port")
    report_date: datetime.date = Field(description="report_date")

class DataFetchTool(BaseTool):
    name: str = "data_fetch_tool"
    description: str = "useful for when you need are asked to fetch dataframe/data for a portfolio"
    args_schema: Optional[ArgsSchema] = DataInput
    return_direct: bool = True

    def _run(
        self, port: str, report_date: datetime.date, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> pd.DataFrame:
        """Use the tool."""
        df = get_trades_data(port, report_date, 10)
        return df

    async def _arun(
        self,
        port: str, report_date: datetime.date,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(port, report_date, run_manager=run_manager.get_sync())
    

class DataTransformationInput(BaseModel):
    port: str = Field(description="port")
    report_date: datetime.date = Field(description="report date")
    transformation_prompt: str = Field(description="user input text to perform data transformation")

class DataTransformationTool(BaseTool):
    name: str = "data_transformation_tool"
    description: str = "strictly use when you are asked to perform manipulations on dataframe, user provides port and report date, dataframes are cached with key dependent of port and report_date"
    args_schema: Optional[ArgsSchema] = DataTransformationInput
    return_direct: bool = True

    def _run(
        self, port: str, report_date: datetime.date, transformation_prompt: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> pd.DataFrame:
        print('function begins')
        """Use the tool."""
        data_id = repr({
            'port': port,
            'report_date': str(report_date)
        })
        df = state_manager.get(data_id)
        agent = create_pandas_dataframe_agent(
            ChatOpenAI(temperature=0, model="gpt-4.1-nano"),
            df, verbose=True, 
            allow_dangerous_code=True
        )
        response = agent.run(transformation_prompt)

        return response

    async def _arun(
        self, port: str, report_date: datetime.date, transformation_prompt: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(port, report_date, transformation_prompt, run_manager=run_manager.get_sync())
        
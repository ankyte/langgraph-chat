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


class ChartInput(BaseModel):
    port: str = Field(description="port")
    report_date: datetime.date = Field(description="report_date")
    chart_type: str = Field(description="chart_type: pie/bar/line/donut/scatter/histogram/area/heatmap/waterfall")

class ChartTool(BaseTool):
    name: str = "chart_tool"
    description: str = "when user asks to generate a chart, you need to figure out port and report_date from past chats, the dataframes to generate charts are cached with key name dependent of port and report_date."
    args_schema: Optional[ArgsSchema] = ChartInput
    return_direct: bool = True

    def _run(
        self, port: str, report_date: datetime.date, chart_type: datetime.date, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> pd.DataFrame:
        """Use the tool."""
        data_id = repr({
            'port': port,
            'report_date': str(report_date)
        })
        return f"{data_id}||{chart_type}"

    async def _arun(
        self, port: str, report_date: datetime.date, chart_type: datetime.date,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> int:
        """Use the tool asynchronously."""
        return self._run(port, report_date, chart_type, run_manager=run_manager.get_sync())
    
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def generate_chart(df, chart_type):
    # Expanded mock data
    data = {
        'Category': df['Trade Date'],
        'Values': df['Net Money']
    }
    ticker = str(df['Ticker'].iloc[0])
    df = pd.DataFrame(data)

    fig, ax = plt.subplots(figsize=(6, 4))

    if chart_type == "bar":
        # # fig, ax = plt.subplots()
        ax.bar(df['Category'], df['Values'])
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "line":
        # # fig, ax = plt.subplots()
        ax.plot(df['Category'], df['Values'], marker='o')
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "pie":
        # fig, ax = plt.subplots()
        ax.pie(df['Values'], labels=df['Category'], autopct="%1.1f%%")
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "donut":
        # fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(
            df['Values'],
            labels=df['Category'],
            autopct='%1.1f%%',
            wedgeprops=dict(width=0.3)
        )
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "scatter":
        # fig, ax = plt.subplots()
        ax.scatter(df['Category'], df['Values'], color='green')
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "histogram":
        # fig, ax = plt.subplots()
        ax.hist(df['Values'], bins=10, color='skyblue', edgecolor='black')
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "box":
        # fig, ax = plt.subplots()
        ax.boxplot(df['Values'])
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "area":
        # fig, ax = plt.subplots()
        ax.fill_between(df['Category'], df['Values'], color='orange', alpha=0.6)
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "heatmap":
        # fig, ax = plt.subplots()
        sns.heatmap(df[['Values']], annot=True, cmap="YlGnBu", ax=ax)
        ax.set_title(ticker)
        st.pyplot(fig)

    elif chart_type == "waterfall":
        cumulative_values = df['Values'].cumsum()
        # fig, ax = plt.subplots()
        ax.bar(df['Category'], df['Values'])
        ax.plot(df['Category'], cumulative_values, color='red', marker='o', linestyle='--')
        ax.set_title(ticker)
        st.pyplot(fig)

    else:
        st.write("Unsupported chart type.")

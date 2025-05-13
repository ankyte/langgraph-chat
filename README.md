.env file

`
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=""
LANGSMITH_PROJECT=""
OPENAI_API_KEY=""
TAVILY_API_KEY=""
`

To run server
`
python -m uvicorn app:app --reload
`

To run client
`
python -m streamlit run ui.py
`
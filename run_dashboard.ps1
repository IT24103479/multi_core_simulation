$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

python -m pip install -r requirements.txt
streamlit run app.py


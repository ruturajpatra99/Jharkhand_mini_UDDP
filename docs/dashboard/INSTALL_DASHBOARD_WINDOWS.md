# Add the Excel dashboard to your existing Windows GitHub folder

Keep your current checkout and its `.git` folder. Use the small `dashboard-code-update.zip` to copy updated files into that checkout, preserving relative paths. Back up local uncommitted edits before replacing a file. The patch changes src/orchestration.py, src/spark_session.py, requirements.txt and documentation, and adds src/excel_dashboard.py and tests. It does not replace your input data or runtime database.

1. Open the same project folder in VS Code PowerShell.
2. Install the new dependency in the environment that already works:

```powershell
.\.venv311\Scripts\python.exe -m pip install openpyxl==3.1.5
```

3. To create the workbook immediately from your already successful run, no Spark or Java startup is required:

```powershell
.\.venv311\Scripts\python.exe -m src.excel_dashboard --work-dir runtime
```

4. Open `runtime\outputs\dashboard\Jharkhand_UDDP_Interactive_Dashboard.xlsx` in Excel. Start on Executive Dashboard. Use the two dropdowns on District Comparison. Formula results recalculate on opening; if needed select Formulas → Calculation Options → Automatic, then Calculate Now.
5. Future full pipeline runs generate the workbook automatically. Set the existing Java/Python terminal environment as in README, then run:

```powershell
.\.venv311\Scripts\python.exe -m src.main --work-dir runtime
```

6. Test just the dashboard generator:

```powershell
.\.venv311\Scripts\python.exe -m pytest tests/test_excel_dashboard.py -q
```

Close the workbook before regeneration; Excel can lock the file on Windows. If a required CSV is missing or changed after publication, the standalone generator reports an error instead of publishing an incomplete dashboard. Scores and category assignments remain those of the existing Gold mart.

The dashboard requires Excel-compatible spreadsheet software to view and interact, but Microsoft Excel is not required to generate it. No macros, slicers, external APIs or Power BI are required.

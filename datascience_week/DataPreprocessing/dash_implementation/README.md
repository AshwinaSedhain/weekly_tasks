pipeline flow:


RAW CSV
   ↓
data_engine.py
   (cleaning + preprocessing)
   ↓
CLEAN DATAFRAME
   ↓
app.py
   (filters + visualization)
   ↓
DASHBOARD (user sees graphs)
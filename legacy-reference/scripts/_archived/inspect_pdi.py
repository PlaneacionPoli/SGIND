import pandas as pd
p='artifacts/debug_cascada/pdi.xlsx'
df=pd.read_excel(p)
print('rows',df.shape)
print(df[['Id','Indicador','Cumplimiento','cumplimiento_pct']].head(20).to_csv(index=False))

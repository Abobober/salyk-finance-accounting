import pandas as pd

rows = [
    ['104', 'Городской налоговый орган'],
    ['105', 'Районный налоговый орган'],
    ['106', 'Центральный налоговый орган'],
]

df = pd.DataFrame(rows)
df.to_excel('tax_org.xlsx', header=False, index=False)
print('Wrote tax_org.xlsx')

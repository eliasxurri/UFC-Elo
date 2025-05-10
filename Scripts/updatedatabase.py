import pandas as pd

# 1. Cargar el dataset original
dataset_original = pd.read_csv('../Datasets/ufc-master-kaggle-original.csv')

# 2. Cargar las nuevas entradas desde un archivo
nuevas_entradas = pd.read_csv('../Datasets/ufc-peleas-2025.csv')

# 3. Concatenar
dataset_actualizado = pd.concat([dataset_original, nuevas_entradas], ignore_index=True)

# 4. Guardar en el archivo original
dataset_actualizado.to_csv('../Datasets/ufc_fight_data.csv', index=False)

print("Nuevas entradas agregadas, broder.")
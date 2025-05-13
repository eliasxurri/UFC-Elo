import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def calculate_elo_per_division(fights, k_base=32):
    elo_scores = {}  # {fighter: {division: elo}}
    fight_counts = {}  # {fighter: {division: count}}
    elo_history = []
    
    for _, row in fights.iterrows():
        fighter_a = row['RedFighter'].strip()
        fighter_b = row['BlueFighter'].strip()
        winner = row['Winner'].strip().upper()
        division = row['WeightClass'].strip()
        date = row['Date']
        
        if fighter_a not in elo_scores:
            elo_scores[fighter_a] = {}
            fight_counts[fighter_a] = {}
        if fighter_b not in elo_scores:
            elo_scores[fighter_b] = {}
            fight_counts[fighter_b] = {}
        
        if division not in elo_scores[fighter_a]:
            if elo_scores[fighter_a]:
                avg_elo = sum(elo_scores[fighter_a].values()) / len(elo_scores[fighter_a])
                elo_scores[fighter_a][division] = avg_elo
            else:
                elo_scores[fighter_a][division] = 1500
            fight_counts[fighter_a][division] = 0
        if division not in elo_scores[fighter_b]:
            if elo_scores[fighter_b]:
                avg_elo = sum(elo_scores[fighter_b].values()) / len(elo_scores[fighter_b])
                elo_scores[fighter_b][division] = avg_elo
            else:
                elo_scores[fighter_b][division] = 1500
            fight_counts[fighter_b][division] = 0
        
        # Guardar el Elo pre-pelea
        ra_pre = elo_scores[fighter_a][division]
        rb_pre = elo_scores[fighter_b][division]
        
        # Calcular el Elo post-pelea
        ea = 1 / (1 + 10 ** ((rb_pre - ra_pre) / 400))
        eb = 1 / (1 + 10 ** ((ra_pre - rb_pre) / 400))
        
        if winner == 'RED':
            sa = 1
            sb = 0
        elif winner == 'BLUE':
            sa = 0
            sb = 1
        else:
            sa = 0.5
            sb = 0.5
        
        k_a = k_base
        k_b = k_base
        
        # Actualizar Elo post-pelea
        elo_scores[fighter_a][division] += k_a * (sa - ea)
        elo_scores[fighter_b][division] += k_b * (sb - eb)
        fight_counts[fighter_a][division] += 1
        fight_counts[fighter_b][division] += 1
        
        # Guardar en el historial con Elo pre-pelea y post-pelea
        elo_history.append({
            'Date': date,
            'fighter_a': fighter_a,
            'fighter_b': fighter_b,
            'division': division,
            'elo_a_pre': ra_pre,
            'elo_b_pre': rb_pre,
            'elo_a_post': elo_scores[fighter_a][division],
            'elo_b_post': elo_scores[fighter_b][division]
        })
    
    return elo_scores, pd.DataFrame(elo_history)

# Cargar y preparar el dataset
fights = pd.read_csv('../Datasets/ufc_fight_data.csv')
fights['Date'] = pd.to_datetime(fights['Date'], format='%d-%m-%y', errors='coerce')
fights = fights.dropna(subset=['Date']).sort_values('Date')

# Calcular Elo por división
elo_scores, elo_history_df = calculate_elo_per_division(fights)

# Unir el Elo pre-pelea al dataset original
fights = fights.merge(elo_history_df[['Date', 'fighter_a', 'fighter_b', 'elo_a_pre', 'elo_b_pre']],
                      left_on=['Date', 'RedFighter', 'BlueFighter'],
                      right_on=['Date', 'fighter_a', 'fighter_b'],
                      how='left')

# Eliminar columnas temporales
fights = fights.drop(columns=['fighter_a', 'fighter_b'], errors='ignore')

# Guardar el dataset actualizado
fights.to_csv('../Datasets/ufc_fight_data_with_elo.csv', index=False)
print("Dataset con Elo pre-pelea guardado en '../Datasets/ufc_fight_data_with_elo.csv'")

# Generar gráficos de tendencias por división
divisions = fights['WeightClass'].unique()

for division in divisions:
    # Filtrar el historial para la división
    division_history = elo_history_df[elo_history_df['division'] == division]
    
    # Obtener los 5 mejores peleadores en la división
    top_5 = division_history.groupby('fighter_a')['elo_a_post'].max().nlargest(5).index.tolist()
    
    # Filtrar el historial para estos peleadores
    top_5_history = division_history[division_history['fighter_a'].isin(top_5)]
    
    # Graficar
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=top_5_history, x='Date', y='elo_a_post', hue='fighter_a', marker='o')
    plt.title(f'Tendencias de Elo para los 5 Mejores Peleadores en {division}')
    plt.xlabel('Fecha')
    plt.ylabel('Rating Elo')
    plt.legend(title='Peleador')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'../Graphs/elo_trends_{division.replace(" ", "_").lower()}.png')
    plt.close()
    print(f"Gráfico de tendencias para {division} guardado en '../Graphs/elo_trends_{division.replace(' ', '_').lower()}.png'")
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
        
        ra = elo_scores[fighter_a][division]
        rb = elo_scores[fighter_b][division]
        
        ea = 1 / (1 + 10 ** ((rb - ra) / 400))
        eb = 1 / (1 + 10 ** ((ra - rb) / 400))
        
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
        
        elo_scores[fighter_a][division] += k_a * (sa - ea)
        elo_scores[fighter_b][division] += k_b * (sb - eb)
        fight_counts[fighter_a][division] += 1
        fight_counts[fighter_b][division] += 1
        
        elo_history.append({
            'Date': date,
            'fighter': fighter_a,
            'division': division,
            'elo': elo_scores[fighter_a][division]
        })
        elo_history.append({
            'Date': date,
            'fighter': fighter_b,
            'division': division,
            'elo': elo_scores[fighter_b][division]
        })
    
    return elo_scores, pd.DataFrame(elo_history)

# Load and prepare the dataset
fights = pd.read_csv('../Datasets/ufc_fight_data.csv')
fights['Date'] = pd.to_datetime(fights['Date'], format='%d-%m-%y', errors='coerce')
fights = fights.dropna(subset=['Date']).sort_values('Date')

# Calculate Elo per division
elo_scores, elo_history_df = calculate_elo_per_division(fights)

# Create a DataFrame for final Elo per fighter per division
elo_data = []
for fighter, divisions in elo_scores.items():
    for division, elo in divisions.items():
        elo_data.append({
            'fighter': fighter,
            'division': division,
            'elo': elo
        })
elo_df = pd.DataFrame(elo_data)

# Save to CSV
elo_df.to_csv('../Datasets/elo_per_division.csv', index=False)
print("Elo per division saved to 'elo_per_division.csv'")

# Get unique divisions
divisions = elo_df['division'].unique()

# For each division, get top 5 fighters and plot their Elo trends
for division in divisions:
    # Get top 5 fighters in this division
    top_5 = elo_df[elo_df['division'] == division].nlargest(5, 'elo')['fighter'].tolist()
    
    # Filter history for these fighters in this division
    division_history = elo_history_df[(elo_history_df['division'] == division) & (elo_history_df['fighter'].isin(top_5))]
    
    # Plot
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=division_history, x='Date', y='elo', hue='fighter', marker='o')
    plt.title(f'Elo Trends for Top 5 Fighters in {division}')
    plt.xlabel('Date')
    plt.ylabel('Elo Rating')
    plt.legend(title='Fighter')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'elo_trends_{division.replace(" ", "_").lower()}.png')
    plt.close()
    print(f"Trend plot for {division} saved as '../Graphs/elo_trends_{division.replace(' ', '_').lower()}.png'")
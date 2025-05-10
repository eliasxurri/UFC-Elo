import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Function to calculate Elo ratings
def calculate_elo_prelim(fights, k_base=32):
    elo_scores = {}
    fight_counts = {}
    elo_history = []
    
    for _, row in fights.iterrows():
        fighter_a = row['RedFighter']
        fighter_b = row['BlueFighter']
        winner = row['Winner']
        method = row['Finish'] if pd.notna(row['Finish']) else 'U-DEC'  # Default to U-DEC if missing
        date = row['Date']
        
        # Initialize Elo for new fighters
        if fighter_a not in elo_scores:
            elo_scores[fighter_a] = 1500
            fight_counts[fighter_a] = 0
        if fighter_b not in elo_scores:
            elo_scores[fighter_b] = 1500
            fight_counts[fighter_b] = 0
            
        # Calculate expected scores
        ra = elo_scores[fighter_a]
        rb = elo_scores[fighter_b]
        ea = 1 / (1 + 10 ** ((rb - ra) / 400))
        eb = 1 / (1 + 10 ** ((ra - rb) / 400))
        
        # Determine actual scores based on Winner
        if winner == 'Red':
            sa = 1
            sb = 0
        elif winner == 'Blue':
            sa = 0
            sb = 1
        else:  # Handle draws or unexpected values
            sa = 0.5
            sb = 0.5
            
        # Adjust K-factor based on experience and finish method
        k_a = k_base * (2 if fight_counts[fighter_a] < 5 else 1.5 if fight_counts[fighter_a] < 20 else 1)
        k_b = k_base * (2 if fight_counts[fighter_b] < 5 else 1.5 if fight_counts[fighter_b] < 20 else 1)
        if method in ['KO/TKO', 'SUB']:
            k_a *= 1.2; k_b *= 1.2
        elif method == 'U-DEC':
            k_a *= 0.9; k_b *= 0.9
        elif method == 'S-DEC':
            k_a *= 0.7; k_b *= 0.7
        elif method == 'M-DEC':
            k_a *= 0.8; k_b *= 0.8
        elif method in ['DQ', 'DQ/TKO']:
            k_a *= 0.5; k_b *= 0.5
        elif method == 'Overturned':
            k_a *= 0; k_b *= 0
        else:  # Other cases
            k_a *= 0.8; k_b *= 0.8
            
        # Update Elo scores
        elo_scores[fighter_a] += k_a * (sa - ea)
        elo_scores[fighter_b] += k_b * (sb - eb)
        fight_counts[fighter_a] += 1
        fight_counts[fighter_b] += 1
        
        # Record history
        elo_history.append({'date': date, 'fighter': fighter_a, 'elo': elo_scores[fighter_a], 'fight_count': fight_counts[fighter_a]})
        elo_history.append({'date': date, 'fighter': fighter_b, 'elo': elo_scores[fighter_b], 'fight_count': fight_counts[fighter_b]})
    
    return elo_scores, pd.DataFrame(elo_history), fight_counts

# Load your dataset (replace with your actual file path)
# fights_df = pd.read_csv('ufc_fight_data.csv', sep='\t')  # Assuming tab-separated based on your example

# For this example, use a subset of your provided data
fights_df = pd.read_csv('../Datasets/ufc_fight_data.csv')  # Reemplazar con tu archivo
fights_df['Date'] = pd.to_datetime(fights_df['Date'])
fights_df = fights_df.sort_values('Date')

# Convert Date to datetime and sort chronologically
fights_df['Date'] = pd.to_datetime(fights_df['Date'], format='%d-%m-%y')
fights_df = fights_df.sort_values('Date')

# Calculate Elo ratings
elo_scores, elo_history_df, fight_counts = calculate_elo_prelim(fights_df)

# Generate fighter stats
fighter_stats = []
all_fighters = set(fights_df['RedFighter']).union(set(fights_df['BlueFighter']))
for fighter in all_fighters:
    past_fights = fights_df[(fights_df['RedFighter'] == fighter) | (fights_df['BlueFighter'] == fighter)]
    wins = len(past_fights[((past_fights['Winner'] == 'Red') & (past_fights['RedFighter'] == fighter)) | 
                           ((past_fights['Winner'] == 'Blue') & (past_fights['BlueFighter'] == fighter))])
    win_ratio = wins / len(past_fights) if len(past_fights) > 0 else 0
    fighter_stats.append({
        'fighter_name': fighter,
        'elo': elo_scores.get(fighter, 1500),
        'fights': fight_counts.get(fighter, 0),
        'wins': wins,
        'win_ratio': win_ratio
    })

fighter_stats_df = pd.DataFrame(fighter_stats)
fighter_stats_df.to_csv('ufc_fighter_stats_prelim.csv', index=False)
print("Top 15 fighters by Elo:")
print(fighter_stats_df.nlargest(15, 'elo')[['fighter_name', 'elo', 'fights', 'wins', 'win_ratio']].round(2))

# Visualize Elo trends for top 5 fighters
top_fighters = fighter_stats_df.nlargest(5, 'elo')['fighter_name'].tolist()
elo_trend_df = elo_history_df[elo_history_df['fighter'].isin(top_fighters)]
plt.figure(figsize=(12, 6))
sns.lineplot(data=elo_trend_df, x='date', y='elo', hue='fighter', marker='o')
plt.axhline(y=1500, color='gray', linestyle='--', label='Initial Elo (1500)')
plt.title('Elo Rating Evolution of Top 15 Fighters')
plt.xlabel('Date')
plt.ylabel('Elo Rating')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('elo_over_time_prelim.png')
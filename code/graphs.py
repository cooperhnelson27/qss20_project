#file to make the same graph made in frequency_graphs.ipynb, but for several more terms. 


import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from frequency_functions import word_frequency_by_party

from paths import RAW, DERIVED, FIGURES

colors = {'Democrat': '#1f4e9c', 'Republican': '#c8102e'}
plt.rcParams['savefig.dpi'] = 300

con = duckdb.connect(str(DERIVED / 'congress.duckdb'))

congresses = list(range(43, 112))

patterns = {
    'Immigration': r"(?i)\bimmigra(tion|nts?)\b",
    'Tariff': r"(?i)\btariffs?\b",
    'Gay': r"(?i)\bgay\b",
    'Conservation': r"(?i)\bconservation\b",
    'Environment': r"(?i)\benvironment(s|al)?\b",
    'Migrants': r"(?i)\bmigrants?\b",
    'National Debt': r"(?i)\bnational debts?\b",
    'Socialism': r"(?i)\bsocialis(m|ts?)\b",
    'Working Class': r"(?i)\bworking[ -]?class(es)?\b",
    'Labor': r"(?i)\blabor(ers?)?\b",
    'Patriotism': r"(?i)\bpatriot(s|ic|ism)\b",
    'Crisis': r"(?i)\bcris[ie]s\b",
    'Christian': r"(?i)\bchristian(s|ity)?\b"
}

for key, value in patterns.items(): 
    print(key)
    rows = []

    for congress in congresses:
        rows.append(word_frequency_by_party(con, value, congress))

    table = pd.concat(rows, ignore_index=True)

    table['year'] = 1789 + 2 * (table['congress'] - 1)

    fig, ax = plt.subplots(figsize=(6, 2.5))

    sns.lineplot(
        data=table,
        x='year',
        y='frequency',
        hue='party',
        palette=colors,
        ax=ax,
    )
    ax.set(
        xlabel = 'Year', 
        ylabel = 'Mentions per 10k Words',
        title = f'{key} Mentions in Congress Over Time'
    )
    ax.spines[['top', 'right']].set_visible(False)

    fig.savefig(FIGURES / f'{key.lower().replace(' ', '_')}_by_party.png', bbox_inches='tight')
    plt.close(fig)



con.close()

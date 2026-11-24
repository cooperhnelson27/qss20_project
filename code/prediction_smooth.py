#basically identical to prediction.ipynb, but iterates over multiple seeds. And averages to get the noise out. 

import os
os.environ['OMP_NUM_THREADS'] = '1'
from pathlib import Path

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
plt.rcParams['savefig.dpi'] = 300

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, confusion_matrix, mean_squared_error)
from sklearn.model_selection import (train_test_split)

from paths import RAW, DERIVED, FIGURES

con = duckdb.connect(str(DERIVED / 'congress.duckdb'), read_only=True)

sample_size = 1000

keys = con.sql('''
SELECT speech_id, party_group, party, congress
FROM everything_but_speeches
WHERE party IN ('D', 'R') AND word_count >= 100
''').df()

congresses = list(range(43, 112))

procedural_terms = {
    'speaker', 'chairman', 'chairwoman', 'chair', 'president', 'madam', 'mr',
    'gentleman', 'gentlemen', 'gentlewoman', 'gentlelady', 'colleague', 'colleagues',
    'senator', 'senators', 'distinguished', 'friend', 'ranking', 'tempore', 'pro',
    'yield', 'yields', 'yielded', 'reclaiming', 'time', 'minutes', 'balance',
    'unanimous', 'consent', 'objection', 'quorum', 'clerk', 'recognized',
    'amendment', 'amendments', 'motion', 'resolution', 'rule', 'rules',
    'committee', 'subcommittee', 'conference', 'report',
    'leader', 'leadership', 'whip', 'side', 'aisle',
}

states_terms = {
    'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado',
    'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho',
    'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine',
    'maryland', 'massachusetts', 'michigan', 'minnesota', 'mississippi',
    'missouri', 'montana', 'nebraska', 'nevada', 'ohio', 'oklahoma', 'oregon',
    'pennsylvania', 'tennessee', 'texas', 'utah', 'vermont', 'virginia',
    'wisconsin', 'wyoming', 'carolina', 'dakota', 'hampshire', 'jersey', 'york', 'rhode'
}

party_terms = {
    'republican', 'republicans', 'democrat', 'democrats'
}

results = []
coefs = []

for seed in range(10):    
    print(f'Starting step {seed+1} of 10')
    random_sample = (
        keys.sample(frac=1, random_state=seed) 
            .groupby(['congress', 'party_group'])
            .head(sample_size)
        )

    #random state is now seed instead of 42. 

    sample = con.sql('''
    SELECT speech_id, congress, party_group, text
    FROM speeches
    JOIN random_sample USING (speech_id)
    ''').df()

    for congress in congresses:
        print(seed, congress)
        first_id = congress * 10000000
        last_id = (congress + 1) * 10000000 - 1

        df = sample.loc[sample['congress'] == congress]

        X_train, X_test, y_train, y_test = train_test_split(
            df['text'], df['party_group'],
            test_size=0.25, stratify=df['party_group'], random_state=seed)   # random state is now the seed. 

        speakers_from_congress = con.sql(f'''
        SELECT DISTINCT lastname
        FROM everything_but_speeches
        WHERE speech_id BETWEEN {first_id} AND {last_id}
        ''').df()


        speakers = set(speakers_from_congress['lastname'].dropna().str.lower().str.findall(r'\b\w\w+\b').explode().dropna())
        stops = list(ENGLISH_STOP_WORDS | speakers | procedural_terms | states_terms | party_terms)

        tfidf_vec = TfidfVectorizer(min_df=5, max_df=0.5, stop_words=stops)
        tfidf_train = tfidf_vec.fit_transform(X_train)
        tfidf_test = tfidf_vec.transform(X_test)

        logit = LogisticRegression(max_iter=2000)
        logit.fit(tfidf_train, y_train)

        words = tfidf_vec.get_feature_names_out() #get the model words out 
        is_rep = (y_train == 'Republican').to_numpy() # boolean series, numpy array fixes index issues . 
        present = tfidf_train > 0   # does each speech contain each word

        coefs.append(pd.DataFrame({
            'congress': congress,
            'seed': seed,
            'word': words,
            'coef': logit.coef_[0],
            'n_rep_docs': np.asarray(present[is_rep].sum(axis=0)).ravel(),
            'n_dem_docs': np.asarray(present[~is_rep].sum(axis=0)).ravel(), # number of democratic training speeches and republican training speeches. 
        }))

        predict = logit.predict(tfidf_test)
        report = classification_report(y_test, predict, output_dict=True)

        results.append({
            'seed': seed,                                
            'congress': congress,
            'accuracy': report['accuracy'],
            'rep_prec': report['Republican']['precision'],
            'rep_recall': report['Republican']['recall'],
            'year': 1789 + 2 * (congress - 1)
        })

        # adds the seed as a column. 

con.close()

ten_runs = pd.DataFrame(results)
ten_runs.to_csv(DERIVED / 'logit_scores_10x.csv', index = False)

coefs_df = pd.concat(coefs, ignore_index=True)
coefs_df.to_parquet(DERIVED / 'model_words.parquet', index=False)


smooth = ten_runs.groupby(['congress', 'year'], as_index=False)[['accuracy', 'rep_prec', 'rep_recall']].mean()

fig, ax = plt.subplots(figsize=(8, 4))

sns.lineplot(
        data=ten_runs,
        x='year',
        y= 'accuracy',
        color = '#3A0CA3',
        ax=ax,
        label = 'Avg Test Accuracy (10 Runs)'
    )
ax.set(
        xlabel = 'Year', 
        ylabel = 'Average Test Accuracy',
        title =  'Logit Party Prediction Accuracy'
    )
ax.axhline(0.5, linestyle='--', color='gray', label='Baseline (50%)')
#ax.axhline(0.544, linestyle='--', color='red', label='95% Confidence Interval')
ax.legend()
ax.spines[['top', 'right']].set_visible(False)

fig.savefig(FIGURES / 'modelfigs' / 'logit_smooth_accuracy.png', bbox_inches='tight')

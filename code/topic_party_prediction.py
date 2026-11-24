# predicting the party for individual topics
# based on prediction.ipynb with some changes. 

import os
os.environ['OMP_NUM_THREADS'] = '1'
from pathlib import Path

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import numpy as np
plt.rcParams['savefig.dpi'] = 300

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (train_test_split)

from paths import RAW, DERIVED, FIGURES
topicfigs = Path(FIGURES / 'topicfigs')
topicfigs.mkdir(exist_ok=True)
con = duckdb.connect(str(DERIVED / 'congress.duckdb'), read_only=True)


''' 
Design:

Similar to the previous regressions, but we are going to run issue specific models over time. Reduced list of topics below. 
Restrict sample to speeches that contain the seach term only. Take a set length, 100 words around it. Control for sample size. Some may be difficult to find enough. 
Then Random Sample down and run the same model/graph sequence as before. 
Run a random speech baseline to find baseline accuracy over time. We sort of already have this, but tailored to this model. 

To increase accuracy, due to lower counts, I am doing ten splits and averaging. Similar to predictions_smooth

'''

congresses = list(range(43, 112))

#reduced list of patterns 
patterns = {
    'Immigration': r"(?i)\bimmigra(tion|nts?)\b",
    'Tariff': r"(?i)\btariffs?\b",
    'Conservation': r"(?i)\bconservation\b",
    'Environment': r"(?i)\benvironment(s|al)?\b",
    'Labor': r"(?i)\blabor(ers?)?\b",
    'Crisis': r"(?i)\bcris[ie]s\b",
    'Abortion': r"(?i)\babortions?\b",
    'Baseline': r"(?i)\b(say|said)\b" #compare just random slices on say/said - nothing topic specific 
}

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

speaker_stops = {}
for congress in congresses:
    first_id = congress * 10000000
    last_id = (congress + 1) * 10000000 - 1

    speakers_from_congress = con.sql(f'''
    SELECT DISTINCT lastname
    FROM everything_but_speeches
    WHERE speech_id BETWEEN {first_id} AND {last_id}
    ''').df()

    speakers = set(speakers_from_congress['lastname'].dropna().str.lower().str.findall(r'\b\w\w+\b').explode().dropna())
    speaker_stops[congress] = list(ENGLISH_STOP_WORDS | speakers | procedural_terms | states_terms | party_terms) #dict of stop words. same logic as prediction.ipynb, with more additions

sample_size = 200   # smaller sample, because fewer speeches. per party per congress. 
rng = np.random.default_rng(42)

def make_window(text, regex):
    # 100 word window around the match. shift if at the edge of a speech. AI assisted in writing this function. 
    words = text.split()
    m = rng.choice(list(regex.finditer(text)))
    idx = len(text[:m.start()].split())
    start = min(max(idx - 50, 0), len(words) - 101)
    return regex.sub(' ', ' '.join(words[start:start + 101]))

results = []
coefs = []

for topic, pattern in patterns.items():
    print(topic)
    regex = re.compile(pattern)
    p = pattern.replace("'", "''")

    # same as prediction_smooth, but filtered to matches instead of random sample 
    # and groups by congress and party, randomize order (reproducibly), and takes the first 300 per group. 
    sample = con.sql(f'''
        SELECT speech_id, congress, party_group, text
        FROM speeches_merged
        WHERE party IN ('D', 'R') AND word_count > 100
          AND regexp_matches(text, '{p}')
        QUALIFY row_number() OVER (
            PARTITION BY congress, party_group ORDER BY hash(speech_id)) <= {sample_size}
    ''').df()

    sample['window'] = sample['text'].map(lambda t: make_window(t, regex))

    for congress in congresses:
        df = sample.loc[sample['congress'] == congress]

        # skip congresses where speeches are too few 
        counts = df['party_group'].value_counts()
        if len(counts) < 2 or counts.min() < sample_size:
            continue
        for seed in range(10): 
            X_train, X_test, y_train, y_test = train_test_split(
                df['window'], df['party_group'],
                test_size=0.25, stratify=df['party_group'], random_state=seed)

            tfidf_vec = TfidfVectorizer(min_df=5, max_df=0.5, stop_words = speaker_stops[congress])
            tfidf_train = tfidf_vec.fit_transform(X_train)
            tfidf_test = tfidf_vec.transform(X_test)

            logit = LogisticRegression(max_iter=2000)
            logit.fit(tfidf_train, y_train)

            words = tfidf_vec.get_feature_names_out() #get the model words out 
            is_rep = (y_train == 'Republican').to_numpy() # boolean series, numpy array fixes index issues . 
            present = tfidf_train > 0   # does each speech contain each word

            coefs.append(pd.DataFrame({
                'topic': topic, #also include the topic in this df. wasn't in the other one. 
                'congress': congress,
                'seed': seed,
                'word': words,
                'coef': logit.coef_[0],
                'n_rep_docs': np.asarray(present[is_rep].sum(axis=0)).ravel(),
                'n_dem_docs': np.asarray(present[~is_rep].sum(axis=0)).ravel(),
            }))

            results.append({
                'topic': topic,
                'seed': seed,
                'congress': congress,
                'accuracy': logit.score(tfidf_test, y_test),
                'year': 1789 + 2 * (congress - 1),
            })

con.close()
topic_scores = pd.DataFrame(results)
topics_avg = topic_scores.groupby(['topic', 'congress', 'year'], as_index=False)['accuracy'].mean()
topic_scores.to_csv(DERIVED / 'topic_logit_scores.csv', index=False)

coefs_df = pd.concat(coefs, ignore_index=True)
coefs_df.to_parquet(DERIVED / 'topic_word_coefs.parquet', index=False)

for topic in patterns:
    data = topic_scores.loc[topic_scores['topic'] == topic]

    fig, ax = plt.subplots(figsize=(8, 4))

    sns.lineplot(
        data=data,
        x='year',
        y= 'accuracy',
        color = '#3A0CA3',
        ax=ax,
        label = 'Avg. Test Accuracy (10 splits)',
        marker='o',
        markersize=4
    )
    ax.set(
        xlabel = 'Year', 
        ylabel = 'Test Accuracy',
        title =  f'Avg Prediction Accuracy: {topic}'
    )
    ax.spines[['top', 'right']].set_visible(False)
    ax.axhline(0.5, linestyle='--', color='gray', label='Baseline (50%)')
    ax.legend()

    fig.savefig(topicfigs / f'{topic}_accuracy.png', bbox_inches='tight')
    plt.close(fig)


#one graph that combines them all, and loses the error bands 

fig, ax = plt.subplots(figsize=(10, 5)) # a bit bigger 
sns.lineplot(
    data=topics_avg,
    x='year',
    y='accuracy',
    hue='topic',
    palette='tab10',
    ax=ax,
    marker='o',
    markersize=3,
    linewidth=1.2,
)

ax.set(
    xlabel='Year',
    ylabel='Test Accuracy',
    title='Avg Prediction Accuracy by Topic (10 splits)'
)

ax.spines[['top', 'right']].set_visible(False)
ax.axhline(0.5, linestyle='--', color='gray', label='Baseline (50%)')
ax.legend(title='Topic', bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False)

fig.savefig(topicfigs / 'all_topics_accuracy.png', bbox_inches='tight')
plt.close(fig)

#crowded. Just keep a few. 

keep = ['Baseline', 'Abortion', 'Immigration', 'Tariff']
data2 = topics_avg.loc[topics_avg['topic'].isin(keep)]

fig, ax = plt.subplots(figsize=(10, 5))

sns.lineplot(
    data=data2,
    x='year',
    y='accuracy',
    hue='topic',
    hue_order=keep,
    palette='tab10',
    ax=ax,
    marker='o',
    markersize=3,
    linewidth=1.2,
)
ax.set(
    xlabel='Year',
    ylabel='Test Accuracy',
    title='Avg Prediction Accuracy: Selected Topics (10 splits)'
)
ax.spines[['top', 'right']].set_visible(False)
ax.axhline(0.5, linestyle='--', color='gray', label='Baseline (50%)')
ax.legend(title='Topic', bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False)

fig.savefig(topicfigs / 'selected_topics_accuracy.png', bbox_inches='tight')
plt.close(fig)
## Data Structure

Broadly speaking, the size of the data means that using the entire thing in pandas would be too difficult and slow to reliably use, as the entire corpus would be likely over 10gb in memory. 

#### **RAW FOLDER** data/raw contains the raw data files. These are not tracked by git and should not be uploaded to github. 

*us_congressional_speeches* holds the speech files. 

*speakermap* holds the files that contain speaker data for each of the speeches. 

They can be merged on speech_id. 

#### **DERIVED FOLDER** contains derived files. Also not tracked by Git. 

*speakermap.duckdb* is one combined database file from the speakermap parquet.

*speakermap.parquet* is the same thing in efficient parquet format. 

*congress.duckdb* is where the combined merge lives. It is mostly references though, so data not duplicated. 

Objects in congress.duckdb: 
- speakermap is the combine database referencing all of the speakermap files. It is a VIEW, so it takes up no space. 
- speeches is the same thing, but for the congressional records. 
- speeches_merged is these two combined on speech_id, minus duplicate variables. Most analysis can come from here. 
- everything_but_speeches is the entire table without the text column, saved in storage. It is much smaller than the actual speech files. Useful for analysis that doesn't require the text. 

*logit_scores.csv* Contains results per congress about the accuracy scores of a tfidf logit model including accuracy, republican precision, and republican recall. 

*logit_scores_10x.csv* accuracy, Republican precision, and Republican recall for every Congress and seed (prediction_smooth.py).

*model_words.parquet* word coefficients from the overall model for every Congress and seed. (prediction_smooth.py).

*topic_logit_scores.csv* accuracy for every topic, Congress, and seed (topic_party_prediction.py).

*topic_word_coefs.parquet* word coefficients from the topic models (topic_party_prediction.py).

Key variables:
- congress = speech_id // 10000000 (the first two or three digits of speech_id).
- year = 1789 + 2 * (congress - 1), the first year of each Congress.
- party_group is Democrat, Republican, or Other. It is missing when there was no match in the merge. 
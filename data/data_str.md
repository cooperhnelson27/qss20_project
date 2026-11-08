### Data Structure

**RAW FOLDER** data/raw contains the raw data files. These are not tracked by git and should not be uploaded to github. 

*us_congressional_speeches* holds the speech files. 

*speakermap* holds the files that contain speaker data for each of the speeches. 

They can be merged on speech_id. 

*party_full.txt* is a short file that gives the keys of the party variable by congress. Sort of a crosswalk or codebook. 

**DERIVED FOLDER** contains derived files. Also not tracked by Git. 

*speakermap.duckdb* is one combined database file for the speakermap txt files. 

*speakermap.parquet* is the same thing in efficient parquet format. 


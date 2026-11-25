# Execution Order: (Scripts 01-04)
This project follows the following workflow:
1. Run 01_data_pull.py to download the speech data.
2. Download hein-bound.zip from Stanford, put it in data/raw/, and run 02_speaker_map_pull.py.
3. Run 03_speakers.ipynb, then 04_merge.ipynb.
4. Run the analysis files (see the Run Order table in the README).

(`01_data_pull.py` and `02_speaker_map_pull.py` must be run from the project root folder)

### You should run the project from a Conda environment that includes all of the necessary packages installed. 

`conda create -n qss20proj -c conda-forge python=3.12 pandas numpy scipy scikit-learn statsmodels matplotlib seaborn plotly jupyterlab ipykernel python-duckdb pyarrow requests beautifulsoup4 lxml python-dotenv pyyaml huggingface_hub`

The name here is qss20proj but that can be changed. Python version should be whichever you have been using, but if far off there may be issues. I have 3.12 so sticking with that. 

Run all code out of this environment/kernel. 

### Speech Data download 

Run the data pull file 01_data_pull in the proper environment to download the files (about 6.4 GB). Might take some time. If it stops or is interrupted, it can be run again and won't redownload files already done. Puts these files into data/raw. For me this took around 10-15 minutes. This file must be run from the project root folder. 

From here forward, the congressional speech data is in data/raw/us_congressional_speeches/data 

### Party data download

Has to be done manually.

https://data.stanford.edu/congress_text

and download the hein-bound.zip, either manually or using curl. 

7gb and took about an hour for me. Do not unzip it after downloading. Put this zip file in data/raw and then run 02_speaker_map_pull.py from the project root folder. 

Once you have the speaker map files, you can delete the zip. 

### Script ordering

Run 03_speakers.ipynb to combine the speakermap into one parquet and get it into duck db as well. 

Run 04_merge.ipynb to begin to merge the text and speaker data. Creates one new file, a duckdb, with a few reference tables and one stored table. 

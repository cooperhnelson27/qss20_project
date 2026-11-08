# Create a new environment for the project in Conda. This will ensure that we have the same compatibility. 

`conda create -n qss20proj -c conda-forge python=3.12 pandas numpy scipy scikit-learn statsmodels matplotlib seaborn plotly jupyterlab ipykernel python-duckdb pyarrow requests beautifulsoup4 lxml python-dotenv pyyaml`

The name here is qss20proj but that can be changed. Python version should be whichever you have been using, but if far off there may be issues. I have 3.12 so sticking with that. 


*Then run* 

conda install -c conda-forge huggingface_hub

Inside the environment. This package is used to download the data. Or just include this in the previous line. 


Run all project code out of this environment. 

# Speech Data download 

#run the data pull code file in the proper environment to download the files. About 6.5 gb. Might take some time. If it stops or is interrupted, it can be run again and won't redownload files already done. Puts these files into data/raw. For me this took around 10-15 minutes. 

From here forward, the congressional speech data is in data/raw/us_congressional_speeches/data 

# Party data download

Has to be done manually

https://data.stanford.edu/congress_text

and download the hein_bound.zip, either manually or using curl. 

7gb and took about an hour for me. Do not unzip it after downloading. Put this file in data/raw and then run speaker_map_pull.py

Once you have the speaker map files, you can delete the zip. 
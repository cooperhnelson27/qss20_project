## Code that pulls the dataset and puts it into data/raw.
## Run from the project root folder (qss20_project) inside the qss20proj conda environment:
##     conda activate qss20proj
##     python code/data_pull.py

"""
All speech files are downloaded from
https://huggingface.co/datasets/Eugleo/us-congressional-speeches
Files go to data/raw/, which is in the gitignore file.
Data is around 6.4 GB so it may take a while.

What the download looks like:
    - 28 parquet files, data/train-00000-of-00028.parquet ... data/train-00027-of-00028.parquet
      Together these are one big table of speeches, split into pieces ("shards").
    - README.md, the dataset description from Hugging Face.
There are no CSVs or other formats in this dataset, just parquet.
"""

from pathlib import Path

from huggingface_hub import snapshot_download

# Global constants
REPO_ID = "Eugleo/us-congressional-speeches"
# Pin the exact version of the dataset. In case the data changes later
# we will all still download the same thing.
REVISION = "51776342f69868c2cc9a82dc74497d98f62008cb"

# Relative paths, so this works for everyone.
# run script from the project root. qss20_project
RAW = Path('data/raw')
OUT = RAW / 'us_congressional_speeches'   # another subfolder for the dataset. 

# confirm we are in the correct folder. 
if not Path('data').exists():
    raise SystemExit("Can't find the data/ folder. Run this from the qss20_project root folder.")

# Make the output folder if it does not exist yet
OUT.mkdir(parents=True, exist_ok=True)

print(f'Downloading {REPO_ID} into {OUT} ...')

# snapshot_download grabs every file in the dataset repo that matches allow_patterns.
#   repo_type='dataset' -> this is a dataset, not a model (the default)
#   revision            -> the pinned version from above
#   local_dir           -> where the files are saved
#   allow_patterns      -> only the parquet files and the README, skip other junk and stuff 
# If the download gets interrupted, just run the script again. Files that already
# finished are skipped, so it picks up where it left off.
snapshot_download(
    repo_id=REPO_ID,
    repo_type='dataset',
    revision=REVISION,
    local_dir=OUT,
    allow_patterns=['*.parquet', 'README.md'],
)

# Print what we ended up with so we can see the download worked.
files = sorted(OUT.glob('data/*.parquet'))
total_gb = sum(f.stat().st_size for f in files) / 1e9
print(f'Done. {len(files)} parquet files, {total_gb:.1f} GB, saved in {OUT / "data"}')

# To read it later
#     pd.read_parquet('data/raw/us_congressional_speeches/data/train-00000-of-00028.parquet')
# or the whole folder at once (needs a lot of memory, ~6 GB on disk):
#     pd.read_parquet('data/raw/us_congressional_speeches/data/')

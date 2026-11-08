## Code that pulls the speaker map files (party, name, state, etc.) out of the Stanford hein-bound zip.
## The Hugging Face speeches are missing party, so we get it from here.
## Run from the project root folder (qss20_project) inside the qss20proj conda environment:
##     conda activate qss20proj
##     python code/speaker_map_pull.py

"""
Source: https://data.stanford.edu/congress_text  (Gentzkow, Shapiro, and Taddy)
Download hein-bound.zip yourself (~7 GB) and put it in data/raw/.

Layout confirmed from the codebook (codebook_v4.pdf on the Stanford page):
NNN = three-digit Congress number, e.g. 043, 097, 111.
    - speeches_NNN.txt          the speech text               -> SKIP (most of the massive unzipped file size)
    - NNN_SpeakerMap.txt        speaker info for each speech  -> KEEP these (69 files)
SpeakerMap files: header row, pipe | separated, no quotes around values.
Columns include speakerid, speech_id, lastname, firstname, chamber, state, gender,

This script just pulls out the speaker files. No need for the rest that we already got from hf more efficiently. 
"""

import shutil
import zipfile
from pathlib import Path

# Run script from the project root, qss20_project.
RAW = Path('data/raw')
ZIP_PATH = RAW / 'hein-bound.zip'          # where you saved the download
OUT = RAW / 'speakermap'        # another subfolder for this dataset

# Set to True to delete the 7 GB zip once the speaker maps are out.
# Left False by default since deleting can't be undone. Check the output first, then flip it.
# likely easiest to just delete manually afterwards if it worked properly. 
DELETE_ZIP = False

# Confirm we are in the correct folder and the zip is where we expect.
if not Path('data').exists():
    raise SystemExit("Can't find the data/ folder. Run this from the qss20_project root folder.")
if not ZIP_PATH.exists():
    raise SystemExit(f"Can't find {ZIP_PATH}. Download hein-bound.zip and put it in data/raw/.")

# Make the output folder if it does not exist yet
OUT.mkdir(parents=True, exist_ok=True)

# Open the zip without extracting it. namelist() is the list of every file path inside.
with zipfile.ZipFile(ZIP_PATH) as zf:

    # Keep only the SpeakerMap files. Matching on the end of the name means it works
    # no matter what folder they sit in inside the zip (e.g. hein-bound/097_SpeakerMap.txt).
    # The zip was made on a Mac, so it also has a hidden junk copy of every file under
    # __MACOSX/ (e.g. __MACOSX/hein-bound/._097_SpeakerMap.txt). Skip those.
    speaker_files = [name for name in zf.namelist()
                     if name.endswith('SpeakerMap.txt') and not name.startswith('__MACOSX')]

    # If nothing matched, the file names are different than expected.
    # Print a few names so we can see what is actually in there and fix the pattern.
    if len(speaker_files) == 0:
        print('No SpeakerMap files found. First 20 files in the zip:')
        print('\n'.join(zf.namelist()[:20]))
        raise SystemExit()

    print(f'Found {len(speaker_files)} SpeakerMap files. Copying to {OUT} ...')

    # The codebook says there should be 69 (one per Congress, 43rd-111th). Warn if not.
    if len(speaker_files) != 69:
        print(f'Heads up: expected 69 SpeakerMap files but found {len(speaker_files)}. Worth checking.')

    # Fix for a flaw in this particular zip. The zip has an index at the end saying where
    # each file starts. Because the zip is over 4 GB and was made on a Mac, many of those
    # locations are off by exactly 4 GiB (2**32 bytes) too far. Python then looks in the
    # wrong spot and raises "BadZipFile: Bad magic number for file header".
    # Every file in a zip starts with the bytes PK\x03\x04, so we look at the listed spot,
    # and if those bytes aren't there, we move back 4 GiB to the real start. Thank you Claude!! 
    raw_zip = open(ZIP_PATH, 'rb')

    # Copy each one out.
    for name in speaker_files:
        info = zf.getinfo(name)
        raw_zip.seek(info.header_offset)
        if raw_zip.read(4) != b'PK\x03\x04':
            info.header_offset -= 2**32

        # zf.open checks each file's checksum (CRC) as it reads, so if the fix pointed
        # to the wrong data we'd get a "Bad CRC" error, not a silently broken file.
        with zf.open(info) as src, open(OUT / Path(name).name, 'wb') as dst:
            shutil.copyfileobj(src, dst)

    raw_zip.close()

# Print what we ended up with so we can see it worked.
files = sorted(OUT.glob('*SpeakerMap.txt'))
total_mb = sum(f.stat().st_size for f in files) / 1e6
print(f'Done. {len(files)} files, {total_mb:.0f} MB, saved in {OUT}')

# Only delete the zip if we asked to AND the copy actually worked.
if DELETE_ZIP and len(files) == len(speaker_files):
    ZIP_PATH.unlink()
    print(f'Deleted {ZIP_PATH}')

# To read one later (from the root folder) with pandas:
#     pd.read_csv('data/raw/speakermap/097_SpeakerMap.txt', sep='|', quoting=3)
# quoting=3 tells pandas the values are not wrapped in quotes, so a stray " in a name won't break a row.
# If you get a UnicodeDecodeError, add encoding='latin-1'.

#script to create graphs that will show the frequency of certain terms in speeches across congresses. 

from pathlib import Path
import duckdb
import pandas as pd

#duck db does the querying, so pandas never has to deal with the huge tables. 

# returns one row of five columns 

def word_frequency(con, pattern, congress):
    # takes a pattern and a congress #, and returns that pattern's frequency along with its congress 
    pattern = pattern.replace("'", "''") #apostrophes break sql apparantly

    #find range of speech_id values for this congress 
    first_id = congress * 10000000
    last_id = (congress + 1) * 10000000 - 1

    table = con.sql(f'''
        SELECT SUM(len(regexp_extract_all(text, '{pattern}'))) AS matches,
        SUM(word_count) AS words,
        10000 * matches / words AS frequency
        FROM speeches_merged
        WHERE speech_id BETWEEN {first_id} AND {last_id} AND party IN ('D', 'R') AND word_count >= 50
    ''').df()

    table['pattern'] = pattern
    table['congress'] = congress
    table = table[['congress', 'pattern', 'matches', 'words', 'frequency']]
    return table 


def word_frequency_by_party(con, pattern, congress): #returns two rows of five columns, one for each party
    # same as above, but breaks it down by party
    pattern = pattern.replace("'", "''") 

    first_id = congress * 10000000
    last_id = (congress + 1) * 10000000 - 1

    table = con.sql(f'''
            SELECT SUM(len(regexp_extract_all(text, '{pattern}'))) AS matches,
            SUM(word_count) AS words,
            10000 * matches / words AS frequency,
            party
            FROM speeches_merged
            WHERE speech_id BETWEEN {first_id} AND {last_id} AND party IN ('D', 'R') AND word_count >= 50
            GROUP BY party
        ''').df()

    table['congress'] = congress
    table['pattern'] = pattern
    table["party"] = table["party"].replace({"D": "Democrat", "R": "Republican"})
    table = table[['congress', 'pattern', 'party', 'matches', 'words', 'frequency']]
    return table


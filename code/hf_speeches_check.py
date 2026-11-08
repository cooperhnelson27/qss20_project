import duckdb

print(duckdb.sql("""
    SELECT CAST(speech_id / 10000000 AS INT) AS congress,
           min(date) AS first_date,
           max(date) AS last_date,
           count(*)  AS n_speeches
    FROM 'data/raw/us_congressional_speeches/data/*.parquet'
    GROUP BY congress
    ORDER BY congress
""").df().to_string())

#prints one row for each congress. Mostly to check the congress/date column to see how much data there is. 
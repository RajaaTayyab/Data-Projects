import sqlite3
import pandas as pd

#loading the datset
df = pd.read_csv("Netflix Movies Dataset/netflix_titles.csv")

#Creating sql db
conn = sqlite3.connect("netflix.db")

#load into table
df.to_sql("netflix", conn, if_exists="replace", index=False)

print("Database has been created")

#5 qeuries

#Query 1 how many movies and tvshows
print("\nquery 1")
print("How many movies and Tv shows")
query1= """
SELECT type, COUNT(*) as total
 FROM netflix
GROUP BY type
"""
print(pd.read_sql_query(query1,conn))

# Query 2 the 10 most recently added titles
print("\n query 2")
print("Recently added Content")
query2 = """
SELECT title, type, country, date_added
FROM netflix
WHERE date_added IS NOT NULL
ORDER BY date_added DESC
LIMIT 10
"""
print(pd.read_sql_query(query2, conn))


#Query 3 Top 10 directors
print("\n query 3")
print("Top 10 Directors")
query3 = """
SELECT director, COUNT(*) as content_count 
FROM netflix 
WHERE director IS NOT NULL 
GROUP BY director 
ORDER BY content_count DESC 
LIMIT 10
"""
print(pd.read_sql_query(query3, conn))

#Query 4 top 10 Countries which have the most content
print("\n query 4")
print("Top 10 counries with most content")
query4 = """
SELECT country, COUNT(*) as count 
FROM netflix 
WHERE country IS NOT NULL 
GROUP BY country 
ORDER BY count DESC 
LIMIT 10
"""
print(pd.read_sql_query(query4, conn))

#Query 5 Top 10 Movies with the highest runtime
print("\n query 5")
print("The top 10 movies with the longest runtime")
query5 = """
SELECT title, duration
FROM netflix
WHERE type = 'Movie'
ORDER BY CAST(REPLACE(duration, ' min', '') AS INTEGER) DESC
LIMIT 10
"""
print(pd.read_sql_query(query5, conn))
# Databricks notebook source
from pyspark.sql.functions import *
from pyspark.sql.types import *
import os
import sys
project_path = os.path.join(os.getcwd(), '..','..')
sys.path.append(project_path)
from utils.transformations import reusable


# COMMAND ----------

# MAGIC %md
# MAGIC ## **DimUser**

# COMMAND ----------

# MAGIC %md
# MAGIC ### **AUTOLOADER**

# COMMAND ----------

df_user = spark.readStream.format("cloudFiles")\
        .option("cloudFiles.format", "parquet")\
        .option("cloudFiles.schemaLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimUser/checkpoint")\
        .option("schemaEvolutionMode", "addNewColumns")\
        .load("abfss://bronze@storagespotify25.dfs.core.windows.net/DimUser")

# COMMAND ----------

display(df_user)

# COMMAND ----------

df_user = df_user.withColumn("user_name",upper(col("user_name")))

# COMMAND ----------

display(df_user)

# COMMAND ----------

df_user_object = reusable()
df_user =df_user_object.dropColumns(df_user,['_rescued_data'])
df_user = df_user.dropDuplicates(['user_id'])
display(df_user)


# COMMAND ----------

df_user.writeStream.format("delta")\
        .outputMode("append")\
        .option("checkpointLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimUser/checkpoint")\
        .trigger(once=True)\
        .option("path","abfss://silver@storagespotify25.dfs.core.windows.net/DimUser/data")\
        .toTable("spotify_catalog.silver.DimUser")

# COMMAND ----------

# MAGIC %md
# MAGIC ## **DimArtist**

# COMMAND ----------

df_artist = spark.readStream.format("cloudFiles")\
        .option("cloudFiles.format", "parquet")\
        .option("cloudFiles.schemaLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimArtist/checkpoint")\
        .option("schemaEvolutionMode", "addNewColumns")\
        .load("abfss://bronze@storagespotify25.dfs.core.windows.net/DimArtist")

# COMMAND ----------

display(df_artist)

# COMMAND ----------

df_artist_obj = reusable()

df_artist = df_artist_obj.dropColumns(df_artist,['_rescued_data'])
df_artist = df_artist.dropDuplicates(['artist_id'])
display(df_artist)


# COMMAND ----------

df_artist.writeStream.format("delta")\
        .outputMode("append")\
        .option("checkpointLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimArtist/checkpoint")\
        .trigger(once=True)\
        .option("path","abfss://silver@storagespotify25.dfs.core.windows.net/DimArtist/data")\
        .toTable("spotify_catalog.silver.DimArtist")

# COMMAND ----------

# MAGIC %md
# MAGIC ## **DimTrack**

# COMMAND ----------

df_track = spark.readStream.format("cloudFiles")\
        .option("cloudFiles.format", "parquet")\
        .option("cloudFiles.schemaLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimTrack/checkpoint")\
        .option("schemaEvolutionMode", "addNewColumns")\
        .load("abfss://bronze@storagespotify25.dfs.core.windows.net/DimTrack")

# COMMAND ----------

df_track = df_track.withColumn("durationFlag",when(col("duration_sec")<150,"low")\
                               .when(col("duration_sec")<300,"medium")\
                               .otherwise("high"))

df_track = df_track.withColumn("track_Name",regexp_replace(col("track_name"),"-"," "))

df_track = reusable().dropColumns(df_track,['_rescued_data'])
df_track = df_track.dropDuplicates(['track_id'])


display(df_track)

# COMMAND ----------

df_track.writeStream.format("delta")\
        .outputMode("append")\
        .option("checkpointLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimTrack/checkpoint")\
        .trigger(once=True)\
        .option("path","abfss://silver@storagespotify25.dfs.core.windows.net/DimTrack/data")\
        .toTable("spotify_catalog.silver.DimTrack")

# COMMAND ----------

# MAGIC %md
# MAGIC ## **DimDate**

# COMMAND ----------

df_date = spark.readStream.format("cloudFiles")\
        .option("cloudFiles.format", "parquet")\
        .option("cloudFiles.schemaLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimDate/checkpoint")\
        .option("schemaEvolutionMode", "addNewColumns")\
        .load("abfss://bronze@storagespotify25.dfs.core.windows.net/DimDate")

# COMMAND ----------

df_date = reusable().dropColumns(df_date,['_rescued_data'])

df_date.writeStream.format("delta")\
        .outputMode("append")\
        .option("checkpointLocation","abfss://silver@storagespotify25.dfs.core.windows.net/DimDate/checkpoint")\
        .trigger(once=True)\
        .option("path","abfss://silver@storagespotify25.dfs.core.windows.net/DimDate/data")\
        .toTable("spotify_catalog.silver.DimDate")


# COMMAND ----------

# MAGIC %md
# MAGIC ## **FactStream**

# COMMAND ----------

df_fact= spark.readStream.format("cloudFiles")\
        .option("cloudFiles.format", "parquet")\
        .option("cloudFiles.schemaLocation","abfss://silver@storagespotify25.dfs.core.windows.net/FactStream/checkpoint")\
        .option("schemaEvolutionMode", "addNewColumns")\
        .load("abfss://bronze@storagespotify25.dfs.core.windows.net/FactStream")

# COMMAND ----------

display(df_fact)

# COMMAND ----------

df_fact =reusable().dropColumns(df_fact,['_rescued_data'])
df_fact = df_fact.dropDuplicates(['stream_id'])
df_fact.writeStream.format("delta")\
        .outputMode("append")\
        .option("checkpointLocation","abfss://silver@storagespotify25.dfs.core.windows.net/FactStream/checkpoint")\
        .trigger(once=True)\
        .option("path","abfss://silver@storagespotify25.dfs.core.windows.net/FactStream/data")\
        .toTable("spotify_catalog.silver.FactStream")


# COMMAND ----------


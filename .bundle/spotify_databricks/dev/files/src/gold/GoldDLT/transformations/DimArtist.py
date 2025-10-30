import dlt

@dlt.table
def dimartist_staging():
    df = spark.readStream.table("spotify_catalog.silver.dimartist")
    return df

dlt.create_streaming_table(name="dimartist")

dlt.create_auto_cdc_flow(
    target="dimartist",
    source="dimartist_staging",
    keys =["artist_id"],
    sequence_by = "updated_at",
    stored_as_scd_type= 2,
    track_history_except_column_list= None,
    name= None,
    once= False
)
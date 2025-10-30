import dlt

@dlt.table
def factstream_staging():
    df = spark.readStream.table("spotify_catalog.silver.factstream")
    return df

dlt.create_streaming_table(name="factstream")

dlt.create_auto_cdc_flow(
    target="factstream",
    source="factstream_staging",
    keys =["stream_id"],
    sequence_by = "stream_timestamp",
    stored_as_scd_type= 1,
    track_history_except_column_list= None,
    name= None,
    once= False
)
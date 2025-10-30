# Databricks notebook source
from jinja2 import Template

# COMMAND ----------

parameters = [

    {
        "table": "spotify_catalog.silver.factstream",
        "alias": "factstream",
        "cols": "factstream.stream_id, factstream.listen_duration"
    },

    {
        "table": "spotify_catalog.silver.dimuser",
        "alias": "dimuser",
        "cols": "dimuser.user_id, dimuser.user_name",
        "condition": "factstream.user_id = dimuser.user_id"
    },

    {
        "table": "spotify_catalog.silver.dimtrack",
        "alias": "dimtrack",
        "cols": "dimtrack.track_id, dimtrack.track_name",
        "condition": "factstream.track_id = dimtrack.track_id"
    }

]

# COMMAND ----------

query_text = """
SELECT
    {% for parm in parameters %}
        {{ parm.cols }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM
    {{ parameters[0]['table'] }} AS {{ parameters[0]['alias'] }}
    {% for parm in parameters[1:] %}
LEFT JOIN
    {{ parm['table'] }} AS {{ parm['alias'] }}
    ON {{ parm['condition'] }}
    {% endfor %}
"""

# COMMAND ----------


from jinja2 import Template

jinja_sql_str = Template(query_text)
query = jinja_sql_str.render(parameters=parameters)
print(query)

# COMMAND ----------

display(spark.sql(query))

# COMMAND ----------


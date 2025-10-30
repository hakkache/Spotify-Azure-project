# Spotify Azure Data Engineering Project

A comprehensive data engineering solution built on Azure cloud services for processing Spotify streaming data using modern data architecture patterns.

## 🏗️ Architecture Overview

This project implements a **Medallion Architecture** with **Incremental Data Processing** using Azure cloud services:

```
Azure SQL Database (Source) → Azure Data Factory → Azure Data Lake Gen2 → Azure Databricks → Unity Catalog
     4 Tables              Orchestration    Bronze/Silver/Gold      Processing         Governance
```

## 📊 Data Flow Architecture

### Source Data (Azure SQL Database)
- **dim_user**: User demographics and subscription details
- **dim_artist**: Artist information and metadata  
- **dim_date**: Date dimension for time-based analytics
- **fact_stream**: Streaming events and play history

### Medallion Architecture Layers

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   BRONZE LAYER  │    │  SILVER LAYER   │    │   GOLD LAYER    │
│                 │    │                 │    │                 │
│ Raw Parquet     │───▶│ Cleaned Delta   │───▶│ SCD Type 2      │
│ Files           │    │ Tables          │    │ Analytics Ready │
│                 │    │                 │    │                 │
│ • Data Lake     │    │ • Validated     │    │ • Aggregated    │
│ • Partitioned   │    │ • Deduplicated  │    │ • Historized    │
│ • Compressed    │    │ • Enriched      │    │ • Optimized     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Incremental Data Pipeline

### AutoLoader Implementation
```
Source Changes → AutoLoader Detection → Stream Processing → Delta Merge → SCD Type 2 Updates
```

**Key Features:**
- **Change Data Capture**: Tracks modifications using watermarks
- **Exactly-Once Processing**: Ensures data consistency
- **Schema Evolution**: Handles structure changes automatically
- **Checkpoint Management**: Enables recovery and restart capabilities

## 🛠️ Technology Stack

### Azure Services
- **Azure Data Factory**: Pipeline orchestration and scheduling
- **Azure Databricks**: Spark-based data processing
- **Azure Data Lake Storage Gen2**: Scalable data storage
- **Azure SQL Database**: Source system with 4 core tables
- **Azure Key Vault**: Secrets and credential management

### Processing Technologies
- **Apache Spark**: Distributed data processing
- **Delta Lake**: ACID transactions for data lakes
- **AutoLoader**: Incremental file ingestion
- **Unity Catalog**: Data governance and lineage

## 📁 Project Structure

```
├── src/
│   ├── bronze/
│   │   └── raw_data_ingestion.py
│   ├── silver/
│   │   └── data_transformation.py
│   ├── gold/
│   │   └── scd_type2_implementation.py
│   └── utils/
│       └── common_functions.py
├── config/
│   ├── databricks_asset_bundle.yml
│   └── pipeline_config.json
├── sql/
│   ├── create_tables.sql
│   └── merge_statements.sql
├── tests/
│   └── unit_tests.py
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Azure subscription with required services
- Databricks workspace configured
- Unity Catalog enabled
- GitHub repository for CI/CD

### Setup Instructions

1. **Clone Repository**
```bash
git clone https://github.com/hakkache/Spotify-Azure-project.git
cd Spotify-Azure-project
```

2. **Configure Databricks Asset Bundle**
```yaml
bundle:
  name: spotify-data-pipeline
  
resources:
  jobs:
    spotify_etl_job:
      name: "Spotify ETL Pipeline"
      job_clusters:
        - job_cluster_key: "main"
          new_cluster:
            spark_version: "13.3.x-scala2.12"
            node_type_id: "Standard_DS3_v2"
            num_workers: 2
```

3. **Deploy with Asset Bundles**
```bash
databricks bundle deploy --target dev
databricks bundle run spotify_etl_job --target dev
```

## 💾 Data Processing Examples

### Bronze Layer - Raw Ingestion
```python
# AutoLoader for incremental processing
df_stream = spark.readStream \
    .format("cloudFiles") \
    .option("cloudFiles.format", "parquet") \
    .option("cloudFiles.schemaLocation", "/mnt/checkpoints/schema") \
    .load("/mnt/datalake/bronze/")
```

### Silver Layer - Data Transformation
```python
# Clean and validate data
df_cleaned = df_raw \
    .filter(col("user_id").isNotNull()) \
    .withColumn("processed_date", current_timestamp()) \
    .dropDuplicates(["user_id", "stream_date"])
```

### Gold Layer - SCD Type 2 Implementation
```python
# Slowly Changing Dimension Type 2
merge_condition = "target.user_id = source.user_id AND target.is_current = true"

delta_table.merge(
    source_df.alias("source"),
    merge_condition
).whenMatchedUpdate(
    condition = "source.subscription_type != target.subscription_type",
    set = {
        "is_current": "false",
        "end_date": "current_date()"
    }
).whenNotMatchedInsert(
    values = {
        "user_id": "source.user_id",
        "subscription_type": "source.subscription_type",
        "start_date": "current_date()",
        "end_date": "null",
        "is_current": "true"
    }
).execute()
```

## 🔧 Configuration Management

### Unity Catalog Setup
```sql
-- Create catalog and schema
CREATE CATALOG IF NOT EXISTS spotify_catalog;
CREATE SCHEMA IF NOT EXISTS spotify_catalog.processed_data;

-- Grant permissions
GRANT USE CATALOG ON CATALOG spotify_catalog TO `data-engineers`;
GRANT CREATE SCHEMA ON CATALOG spotify_catalog TO `data-engineers`;
```

### Pipeline Configuration
```json
{
  "source_config": {
    "sql_server": "spotify-sql-server.database.windows.net",
    "database": "SpotifyDB",
    "tables": ["dim_user", "dim_artist", "dim_date", "fact_stream"]
  },
  "processing_config": {
    "batch_size": 10000,
    "checkpoint_location": "/mnt/checkpoints/",
    "trigger_interval": "5 minutes"
  }
}
```

## 📈 Monitoring and Optimization

### Performance Metrics
- **Data Freshness**: < 5 minutes latency
- **Processing Throughput**: 1M+ records/hour
- **Error Rate**: < 0.1%
- **Cost Optimization**: Auto-scaling clusters

### Data Quality Checks
```python
# Implement data validation
def validate_data_quality(df):
    null_check = df.filter(col("user_id").isNull()).count()
    duplicate_check = df.count() - df.dropDuplicates().count()
    
    if null_check > 0 or duplicate_check > 0:
        raise Exception("Data quality issues detected")
```

## 🔐 Security and Governance

### Access Control
- **Unity Catalog**: Fine-grained permissions
- **Azure AD Integration**: Single sign-on
- **Key Vault**: Credential management
- **Network Security**: Private endpoints

### Data Lineage
- Automatic tracking through Unity Catalog
- Column-level lineage for compliance
- Impact analysis for changes

## 🚀 Deployment

### CI/CD with GitHub Actions
```yaml
name: Deploy Databricks Asset Bundle
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Bundle
        run: |
          databricks bundle deploy --target prod
```

## 📚 Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [Data Dictionary](docs/data-dictionary.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions and support:
- Create an issue in this repository
- Contact the data engineering team
- Check the troubleshooting guide

---

**Built with ❤️ using Azure Cloud Services and Modern Data Engineering practices**
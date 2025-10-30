# Spotify Azure Data Engineering Project

A comprehensive data engineering solution built on Azure cloud services for processing Spotify streaming data using modern data architecture patterns and Databricks Delta Live Tables (DLT).

## 🏗️ Architecture Overview

This project implements a **Medallion Architecture** with **Incremental Data Processing** using Azure cloud services and Databricks Delta Live Tables:

```
Azure SQL Database (Source) → Azure Data Factory → Azure Data Lake Gen2 → Databricks DLT → Unity Catalog
     5 Tables                   Orchestration        Bronze/Silver/Gold      Processing        Governance
```

## 📊 Data Flow Architecture

### Source Data (Azure SQL Database)
- **DimUser**: User demographics and subscription details
- **DimArtist**: Artist information and metadata
- **DimDate**: Date dimension for time-based analytics
- **DimTrack**: Track information and metadata
- **FactStream**: Streaming events and play history

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

### Azure Data Factory + AutoLoader Implementation
```
Source Changes → ADF Triggers → AutoLoader Detection → Stream Processing → Delta Merge → SCD Type 2 Updates
```

**Key Features:**
- **Change Data Capture**: Tracks modifications using watermarks
- **Exactly-Once Processing**: Ensures data consistency
- **Schema Evolution**: Handles structure changes automatically
- **Checkpoint Management**: Enables recovery and restart capabilities

## 🛠️ Technology Stack

### Azure Services
- **Azure Data Factory**: Pipeline orchestration and scheduling
- **Azure Databricks**: Spark-based data processing with DLT
- **Azure Data Lake Storage Gen2**: Scalable data storage
- **Azure SQL Database**: Source system with 5 core tables
- **Azure Key Vault**: Secrets and credential management

### Processing Technologies
- **Apache Spark**: Distributed data processing
- **Delta Lake**: ACID transactions for data lakes
- **Delta Live Tables (DLT)**: Declarative ETL framework
- **AutoLoader**: Incremental file ingestion
- **Unity Catalog**: Data governance and lineage

## 📁 Project Structure

```
Spotify-Azure-project/
├── .bundle/
│   └── spotify_databricks/
│       └── dev/
│           ├── files/
│           │   ├── src/
│           │   │   ├── gold/
│           │   │   │   └── GoldDLT/
│           │   │   │       ├── transformations/
│           │   │   │       │   ├── DimArtist.py
│           │   │   │       │   ├── DimDate.py
│           │   │   │       │   ├── DimTrack.py
│           │   │   │       │   ├── DimUser.py
│           │   │   │       │   └── FactStream.py
│           │   │   │       └── utilities/
│           │   │   │           └── utils.py
│           │   │   └── silver/
│           │   │       └── Silver_Dimensions.py
│           │   ├── utils/
│           │   │   └── transformations.py
│           │   ├── resources/
│           │   │   ├── spotify_databricks.job.yml
│           │   │   └── spotify_databricks.pipeline.yml
│           │   ├── databricks.yml
│           │   ├── pyproject.toml
│           │   └── requirements.txt
├── dataset/
│   ├── AzureSQLDataSet.json
│   ├── JSON_DYNAMIC.json
│   └── Parquet_dynamic.json
├── factory/
│   └── ADF-Spotify2025.json
├── linkedService/
│   ├── AZDataLakeConn.json
│   └── AZSQLConn.json
├── pipeline/
│   ├── Incremental_ingestion.json
│   └── Incremental_loop.json
├── manifest.mf
├── publish_config.json
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Azure subscription with required services
- Databricks workspace configured
- Unity Catalog enabled
- GitHub repository for CI/CD
- Python 3.10+ environment

### Setup Instructions

1. **Clone Repository**
```bash
git clone https://github.com/hakkache/Spotify-Azure-project.git
cd Spotify-Azure-project
```

2. **Configure Databricks Asset Bundle**
```yaml
# databricks.yml
bundle:
  name: spotify_databricks
  uuid: your-unique-id

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://your-databricks-workspace.azuredatabricks.net
      root_path: /Workspace/Users/your-user/.bundle/${bundle.name}/${bundle.target}
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Deploy with Asset Bundles**
```bash
databricks bundle deploy --target dev
databricks bundle run spotify_etl_job --target dev
```

## 💾 Data Processing Examples

### Bronze Layer - Raw Ingestion (AutoLoader)
```python
# AutoLoader for incremental processing
df_stream = spark.readStream.format("cloudFiles") \
    .option("cloudFiles.format", "parquet") \
    .option("cloudFiles.schemaLocation", "abfss://silver@storage/checkpoint") \
    .option("schemaEvolutionMode", "addNewColumns") \
    .load("abfss://bronze@storage/DimUser")
```

### Silver Layer - Data Transformation
```python
# Clean and validate data
df_user = df_user.withColumn("user_name", upper(col("user_name")))
df_user = df_user_object.dropColumns(df_user, ['_rescued_data'])
df_user = df_user.dropDuplicates(['user_id'])

# Write to Silver layer
df_user.writeStream.format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "abfss://silver@storage/checkpoint") \
    .trigger(once=True) \
    .toTable("spotify_catalog.silver.DimUser")
```

### Gold Layer - Delta Live Tables SCD Type 2
```python
import dlt

# Data quality expectations
expectations = {
    "rule_1": "user_id IS NOT NULL"
}

@dlt.table
@dlt.expect_all_or_drop(expectations)
def dimuser_staging():
    df = spark.readStream.table("spotify_catalog.silver.dimuser")
    return df

# Create SCD Type 2 flow
dlt.create_auto_cdc_flow(
    target="dimuser",
    source="dimuser_staging",
    keys=["user_id"],
    sequence_by="updated_at",
    stored_as_scd_type=2,
    track_history_except_column_list=None,
    name=None,
    once=False
)
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

### Dependencies (pyproject.toml)
```toml
[project]
name = "spotify_databricks"
version = "0.0.1"
requires-python = ">=3.10,<=3.13"

[dependency-groups]
dev = [
    "pytest",
    "databricks-dlt",
    "databricks-connect>=15.4,<15.5",
]
```

### Data Quality Checks
```python
# Implement data validation in DLT
expectations = {
    "valid_user_id": "user_id IS NOT NULL",
    "valid_stream_date": "stream_date IS NOT NULL",
    "positive_duration": "duration_sec > 0"
}

@dlt.expect_all_or_drop(expectations)
def clean_fact_stream():
    return spark.readStream.table("spotify_catalog.bronze.factstream")
```

## 🔐 Security and Governance

### Access Control
- **Unity Catalog**: Fine-grained permissions and data governance
- **Azure AD Integration**: Single sign-on authentication
- **Key Vault**: Secure credential management
- **Network Security**: Private endpoints and VNet integration

### Data Lineage
- Automatic tracking through Unity Catalog
- Column-level lineage for compliance
- Impact analysis for schema changes

## 🚀 Deployment

### Azure Data Factory Pipelines
The project includes two main ADF pipelines:
- **Incremental_ingestion.json**: Handles data extraction from Azure SQL to Data Lake
- **Incremental_loop.json**: Orchestrates the incremental processing workflow

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
      - uses: actions/checkout@v3
      - name: Setup Databricks CLI
        run: |
          curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
      - name: Deploy Bundle
        run: |
          databricks bundle deploy --target prod
        env:
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
```

## 📈 Key Features Implemented

### Data Quality & Validation
- **DLT Expectations**: Automated data quality checks
- **Schema Evolution**: Automatic handling of schema changes
- **Deduplication**: Removal of duplicate records at each layer

### Performance Optimization
- **Delta Lake**: Optimized storage with ACID transactions
- **Partitioning**: Efficient data organization
- **Z-Ordering**: Improved query performance
- **Checkpointing**: Reliable stream processing

### Monitoring & Observability
- **DLT Pipeline Monitoring**: Built-in monitoring and alerting
- **Unity Catalog Lineage**: End-to-end data lineage tracking
- **Azure Monitor**: Infrastructure monitoring integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Project Highlights

- ✅ **Medallion Architecture**: Bronze, Silver, Gold layers
- ✅ **Delta Live Tables**: Declarative ETL framework
- ✅ **Incremental Processing**: Efficient data pipeline
- ✅ **SCD Type 2**: Historical data tracking
- ✅ **Data Quality**: Built-in validation and expectations
- ✅ **Unity Catalog**: Data governance and security
- ✅ **Azure Integration**: Full Azure ecosystem utilization

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using Azure Cloud Services, Databricks Delta Live Tables, and Modern Data Engineering practices**
# Spotify Azure Data Engineering Project

A comprehensive data engineering solution built on Azure cloud services for processing Spotify streaming data using modern data architecture patterns, advanced Azure Data Factory strategies, and Databricks Delta Live Tables (DLT).

## 🏗️ Architecture Overview

This project implements a **Medallion Architecture** with **Advanced Incremental Data Processing** using Azure cloud services and sophisticated ADF orchestration patterns:

```
Azure SQL Database (Source) → Azure Data Factory → Azure Data Lake Gen2 → Databricks DLT → Unity Catalog
     5 Tables                 Advanced Orchestration  Bronze/Silver/Gold    Processing       Governance
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

## 🔧 Azure Data Factory Advanced Strategies

### 1. **Parameterized Pipeline Architecture**

#### Master Pipeline (Incremental_loop.json)
```json
{
  "parameters": {
    "loop_input": {
      "type": "array",
      "defaultValue": [
        {
          "schema": "dbo",
          "table": "DimUser",
          "cdc_col": "updated_at",
          "from_date": ""
        },
        {
          "schema": "dbo", 
          "table": "FactStream",
          "cdc_col": "stream_timestamp",
          "from_date": ""
        }
      ]
    }
  }
}
```

#### Key Features:
- **Dynamic Table Processing**: Single pipeline handles multiple tables
- **Configurable CDC Columns**: Each table can have different change tracking columns
- **Flexible Schema Support**: Supports multiple database schemas
- **Backfill Capability**: `from_date` parameter enables historical data loading

### 2. **Dynamic Dataset Strategy**

#### Parameterized Parquet Dataset
```json
{
  "name": "Parquet_dynamic",
  "parameters": {
    "container": { "type": "string" },
    "folder": { "type": "string" },
    "file": { "type": "string" }
  },
  "typeProperties": {
    "location": {
      "fileName": { "value": "@dataset().file" },
      "folderPath": { "value": "@dataset().folder" },
      "fileSystem": { "value": "@dataset().container" }
    }
  }
}
```

#### Benefits:
- **Single Dataset Definition**: Reusable across all tables and layers
- **Dynamic Path Generation**: Runtime path construction based on parameters
- **Cost Optimization**: Reduces ADF resource consumption
- **Maintenance Efficiency**: One dataset to maintain instead of multiple

### 3. **Advanced Change Data Capture (CDC) Implementation**

#### CDC Tracking Mechanism
```sql
-- Dynamic CDC Query with Parameterization
SELECT * FROM @{item().schema}.@{item().table} 
WHERE @{item().cdc_col} > '@{if(empty(item().from_date), activity('last_cdc').output.value[0].cdc, item().from_date)}'
```

#### CDC State Management
```json
// CDC Checkpoint Storage
{
  "container": "bronze",
  "folder": "@{item().table}_cdc",
  "file": "cdc.json"
}
```

#### Key CDC Features:
- **Watermark-based Processing**: Tracks last processed timestamp per table
- **Backfill Support**: Can process historical data from specific dates
- **Fault Tolerance**: Maintains CDC state for recovery
- **Cross-table Consistency**: Independent CDC tracking per table

### 4. **Smart File Management & Optimization**

#### Empty File Cleanup Strategy
```json
{
  "name": "DeleteEmptyFile",
  "type": "Delete",
  "condition": "@greater(activity('AzureSQLToLake').output.dataRead,0)",
  "ifFalseActivities": [
    {
      "dataset": "Parquet_dynamic",
      "parameters": {
        "file": "@concat(item().table,'_',variables('current'))"
      }
    }
  ]
}
```

#### File Naming Convention
```
Pattern: {TableName}_{Timestamp}.parquet
Example: DimUser_2025-10-30T14:30:00Z.parquet
```

### 5. **ForEach Loop with Parallel Processing**

#### Parallel Table Processing
```json
{
  "name": "ForEach1",
  "type": "ForEach",
  "typeProperties": {
    "items": "@pipeline().parameters.loop_input",
    "isSequential": false,
    "batchCount": 20,
    "activities": [...]
  }
}
```

#### Advantages:
- **Concurrent Execution**: Multiple tables processed simultaneously
- **Scalable Architecture**: Easily add new tables to processing
- **Resource Optimization**: Efficient use of ADF compute resources
- **Reduced Processing Time**: Parallel execution reduces total runtime

### 6. **Error Handling & Monitoring**

#### Pipeline Failure Alerting
```json
{
  "name": "Alert",
  "type": "WebActivity",
  "dependsOn": [
    {
      "activity": "ForEach1",
      "dependencyConditions": ["Failed"]
    }
  ],
  "typeProperties": {
    "method": "POST",
    "url": "https://prod-28.northcentralus.logic.azure.com/workflows/.../triggers/...",
    "body": {
      "pipeline_name": "@{pipeline().Pipeline}",
      "pipeline_id": "@{pipeline().RunId}"
    }
  }
}
```

#### Monitoring Features:
- **Logic Apps Integration**: Automated failure notifications
- **Pipeline Tracking**: Unique run ID tracking
- **Dependency-based Execution**: Smart failure handling
- **Custom Alert Payloads**: Detailed error information

### 7. **Backfilling Strategy**

#### Historical Data Loading
```json
// Backfill Configuration Example
{
  "schema": "dbo",
  "table": "FactStream", 
  "cdc_col": "stream_timestamp",
  "from_date": "2024-01-01"  // Backfill from specific date
}
```

#### Backfill Process:
1. **Set from_date**: Specify historical start date
2. **Bypass CDC**: Uses from_date instead of last CDC value
3. **Incremental Processing**: Processes data in chunks
4. **State Update**: Updates CDC after successful load

### 8. **Performance Optimization Strategies**

#### Query Optimization
- **Partition Elimination**: Leverages SQL Server partitioning
- **Index Utilization**: Optimized WHERE clauses on CDC columns
- **Batch Size Control**: Configurable chunk sizes for large tables
- **Connection Pooling**: Efficient database connection management

#### Storage Optimization
- **Snappy Compression**: Parquet files with snappy compression
- **Partitioning Strategy**: Date-based partitioning in Data Lake
- **File Size Management**: Optimal file sizes for Spark processing
- **Delta Lake Integration**: ACID transactions and performance features

## 🔄 Incremental Data Pipeline Flow

### Complete Pipeline Execution Flow
```
1. Pipeline Trigger → 2. Parameter Resolution → 3. ForEach Table Loop
                                                      ↓
8. CDC State Update ← 7. Data Validation ← 6. File Management ← 5. Data Copy
                                                      ↓
                      9. Success/Failure Notification
```

### Detailed Step Breakdown:

1. **Trigger Activation**: Scheduled or event-based pipeline start
2. **Dynamic Parameter Loading**: Table configurations loaded from parameters
3. **Parallel Table Processing**: ForEach loop initiates concurrent processing
4. **CDC Lookup**: Retrieves last processed timestamp per table
5. **Incremental Data Copy**: Extracts only changed records
6. **Smart File Management**: Creates or deletes files based on data presence
7. **Data Validation**: Ensures data quality and completeness
8. **CDC State Update**: Updates watermark for next execution
9. **Monitoring & Alerting**: Success/failure notifications

## 🛠️ Technology Stack

### Azure Services
- **Azure Data Factory**: Advanced pipeline orchestration with parameterization
- **Azure Databricks**: Spark-based data processing with DLT
- **Azure Data Lake Storage Gen2**: Scalable data storage with hierarchical namespace
- **Azure SQL Database**: Source system with CDC capabilities
- **Azure Key Vault**: Secrets and credential management
- **Azure Logic Apps**: Automated alerting and notifications

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
│           │   ├── resources/
│           │   │   ├── spotify_databricks.job.yml
│           │   │   └── spotify_databricks.pipeline.yml
│           │   ├── databricks.yml
│           │   ├── pyproject.toml
│           │   └── requirements.txt
├── dataset/                    # ADF Dynamic Datasets
│   ├── AzureSQLDataSet.json   # Source SQL dataset
│   ├── JSON_DYNAMIC.json      # Parameterized JSON dataset
│   └── Parquet_dynamic.json   # Parameterized Parquet dataset
├── factory/
│   └── ADF-Spotify2025.json   # Main ADF resource definition
├── linkedService/              # ADF Connection Definitions
│   ├── AZDataLakeConn.json    # Data Lake connection
│   └── AZSQLConn.json         # SQL Database connection
├── pipeline/                   # ADF Pipeline Definitions
│   ├── Incremental_ingestion.json  # Single table processing
│   └── Incremental_loop.json       # Multi-table orchestration
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

2. **Configure Azure Data Factory**
```bash
# Deploy ADF pipelines and datasets
az datafactory pipeline create --factory-name "your-adf" --name "Incremental_loop" --pipeline @pipeline/Incremental_loop.json
```

3. **Configure Databricks Asset Bundle**
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

4. **Deploy with Asset Bundles**
```bash
databricks bundle deploy --target dev
databricks bundle run spotify_etl_job --target dev
```

## 💾 Data Processing Examples

### Azure Data Factory - Dynamic Processing
```json
// Dynamic SQL Query with CDC
{
  "sqlReaderQuery": {
    "value": "SELECT * FROM @{item().schema}.@{item().table} WHERE @{item().cdc_col} > '@{if(empty(item().from_date), activity('last_cdc').output.value[0].cdc, item().from_date)}'",
    "type": "Expression"
  }
}
```

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
# Clean and validate data with deduplication
df_user = df_user.withColumn("user_name", upper(col("user_name")))
df_user = df_user_object.dropColumns(df_user, ['_rescued_data'])
df_user = df_user.dropDuplicates(['user_id'])

# Write to Silver layer with checkpointing
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

# Create SCD Type 2 flow with auto CDC
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

### ADF Pipeline Parameters
```json
{
  "parameters": {
    "loop_input": {
      "type": "array",
      "defaultValue": [
        {
          "schema": "dbo",
          "table": "DimUser", 
          "cdc_col": "updated_at",
          "from_date": ""
        }
      ]
    }
  }
}
```

### Dynamic Dataset Configuration
```json
{
  "parameters": {
    "container": { "type": "string" },
    "folder": { "type": "string" },
    "file": { "type": "string" }
  }
}
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

## 🚀 Deployment & Operations

### ADF Pipeline Scheduling
```json
{
  "triggers": [
    {
      "name": "DailyTrigger",
      "type": "ScheduleTrigger",
      "typeProperties": {
        "recurrence": {
          "frequency": "Day",
          "interval": 1,
          "startTime": "2025-01-01T02:00:00Z"
        }
      }
    }
  ]
}
```

### Monitoring & Alerting
- **Pipeline Run Monitoring**: Built-in ADF monitoring
- **Logic Apps Integration**: Custom failure notifications
- **Azure Monitor**: Infrastructure and performance monitoring
- **Data Quality Alerts**: DLT expectation violations

### CI/CD with GitHub Actions
```yaml
name: Deploy ADF and Databricks
on:
  push:
    branches: [main]

jobs:
  deploy-adf:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy ADF
        run: |
          az datafactory pipeline create --factory-name ${{ secrets.ADF_NAME }} \
            --name "Incremental_loop" --pipeline @pipeline/Incremental_loop.json
  
  deploy-databricks:
    runs-on: ubuntu-latest  
    steps:
      - uses: actions/checkout@v3
      - name: Deploy Bundle
        run: |
          databricks bundle deploy --target prod
        env:
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
```

## 📈 Key Features Implemented

### Azure Data Factory Advanced Features
- ✅ **Parameterized Pipelines**: Dynamic table processing
- ✅ **ForEach Parallel Processing**: Concurrent table loading
- ✅ **Dynamic Datasets**: Reusable dataset definitions
- ✅ **CDC State Management**: Watermark-based change tracking
- ✅ **Smart File Management**: Empty file cleanup
- ✅ **Error Handling**: Logic Apps integration for alerts
- ✅ **Backfill Capability**: Historical data loading support

### Data Quality & Validation
- ✅ **DLT Expectations**: Automated data quality checks
- ✅ **Schema Evolution**: Automatic handling of schema changes
- ✅ **Deduplication**: Removal of duplicate records at each layer

### Performance Optimization
- ✅ **Delta Lake**: Optimized storage with ACID transactions
- ✅ **Partitioning**: Efficient data organization
- ✅ **Parallel Processing**: Concurrent pipeline execution
- ✅ **Checkpointing**: Reliable stream processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Project Highlights

- ✅ **Advanced ADF Orchestration**: Sophisticated pipeline patterns
- ✅ **Parameterized Architecture**: Highly configurable and maintainable
- ✅ **Change Data Capture**: Efficient incremental processing
- ✅ **Backfill Support**: Historical data loading capabilities
- ✅ **Dynamic Datasets**: Cost-effective and scalable design
- ✅ **Error Handling**: Robust monitoring and alerting
- ✅ **Medallion Architecture**: Bronze, Silver, Gold layers
- ✅ **Delta Live Tables**: Declarative ETL framework
- ✅ **Unity Catalog**: Data governance and security

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using Advanced Azure Data Factory Patterns, Databricks Delta Live Tables, and Modern Data Engineering Best Practices**
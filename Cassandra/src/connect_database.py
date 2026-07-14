import json
import os
import uuid
from datetime import datetime, timezone
from astrapy import DataAPIClient
from astrapy.info import CreateTableDefinition, TablePrimaryKeyDescriptor


TOKEN_JSON   = ".\\Test-token_Cassandra.json"
ENDPOINT     = "https://d12a0ace-b344-4adf-92ea-de2c692082de-us-east-2.apps.astra.datastax.com"
KEYSPACE     = "Test"
TABLE_NAME   = "sensor_readings"
DATA_FILE    = ".\\sensor_data.json"


def get_db():
    with open(TOKEN_JSON) as f:
        token_data = json.load(f)
    client = DataAPIClient(token_data["token"])

    return client.get_database(ENDPOINT, keyspace=KEYSPACE)


def create_table(db):
    """Create a wide-column sensor_readings table (partition: sensor_id, cluster: reading_id)."""
    table_def = CreateTableDefinition.coerce({
        "columns": {
            "sensor_id":    "text",       # partition key  → all rows for a sensor on one node
            "reading_id":   "uuid",       # clustering key → unique per reading
            "reading_time": "timestamp",  # wide column
            "location":     "text",
            "temperature":  "float",
            "humidity":     "float",
        },
        "primaryKey": {
            "partitionBy":   ["sensor_id"],
            "partitionSort": {"reading_id": 1},   # ascending cluster order
        },
    })

    table = db.create_table(TABLE_NAME, definition=table_def, if_not_exists=True)
    print(f"✅ Table '{TABLE_NAME}' ready.")
    return table


def load_and_insert(table):
    """Read rows from sensor_data.json and insert them into the table."""
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Data file not found: {DATA_FILE}")

    with open(DATA_FILE) as f:
        records = json.load(f)

    rows = [
        {
            **record,
            "reading_id":   str(uuid.uuid4()),
            "reading_time": datetime.now(timezone.utc).isoformat(),
        }
        for record in records
    ]

    result = table.insert_many(rows)
    print(f"✅ Inserted {len(result.inserted_ids)} rows into '{TABLE_NAME}'.")


def read_table(table):
    """Read back all rows and print them."""
    print(f"\n📋 Rows in '{TABLE_NAME}':")
    for row in table.find({}):
        print(f"  sensor={row['sensor_id']}  temp={row['temperature']}°C  "
              f"humidity={row['humidity']}%  loc={row['location']}  "
              f"time={row['reading_time']}")


def test_connection():
    """Test the connection to Astra DB and list available tables."""
    print("🔄 Connecting to Astra DB...")
    db = get_db()
    print(f"✅ Connection successful  →  {db.name}")
    tables = db.list_table_names()
    print(f"📋 Tables in keyspace '{KEYSPACE}': {tables if tables else '(none yet)'}")
    return db


def write_to_db():
    """Create table (if needed) and insert data from sensor_data.json."""
    print("🔄 Connecting to Astra DB...")
    db = get_db()
    print(f"✅ Connected  →  {db.name}")
    table = create_table(db)
    load_and_insert(table)
    read_table(table)


if __name__ == "__main__":
    print("\nWhat would you like to do?")
    print("  1. Test connection")
    print("  2. Write data to DB")
    choice = input("\nEnter option (1 or 2): ").strip()

    if choice == "1":
        test_connection()
    elif choice == "2":
        write_to_db()
    else:
        print("❌ Invalid option. Please enter 1 or 2.")
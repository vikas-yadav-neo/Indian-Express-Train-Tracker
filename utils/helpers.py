from pyspark.sql.types import (
    StringType, IntegerType, LongType, DoubleType, FloatType, BooleanType, TimestampType, DateType,
    ArrayType, MapType, StructType
)
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import SQLAlchemyError



def drop_columns_spark(df, columns_to_drop):
    """
    Drop columns from a Spark DataFrame.
    """
    return df.drop(*columns_to_drop)



def create_table_dynamic(db_url: str, table_name: str, columns: list, indexes: list = None):
    """
    Dynamically create a table with optional indexes.
    """
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    type_map = {
        "integer": Integer,
        "string": lambda length=255: String(length),
        "datetime": DateTime,
        "float": Float,
        "array": lambda: ARRAY(Integer)
    }

    column_objs = []
    for col in columns:
        col_type_key = col["type"].lower()
        if col_type_key not in type_map:
            raise ValueError(f"Unsupported column type: {col['type']}")

        if col_type_key == "string":
            col_type = type_map[col_type_key](col.get("length", 255))
        elif col_type_key == "array":
            col_type = type_map[col_type_key]()
        else:
            col_type = type_map[col_type_key]

        fk = ForeignKey(col["foreign_key"]) if "foreign_key" in col else None
        args = [col["name"], col_type]
        if fk:
            args.append(fk)

        column_objs.append(
            Column(
                *args,
                primary_key=col.get("primary_key", False),
                nullable=col.get("nullable", True),
                autoincrement=col.get("autoincrement", False),
                unique=col.get("unique", False),
                default=col.get("default", None),
            )
        )

    table = Table(table_name, metadata, *column_objs)

    if indexes:
        for idx in indexes:
            Index(idx["name"], *[table.c[col] for col in idx["columns"]])

    try:
        metadata.create_all(engine)
        print(f"✅ Table '{table_name}' created successfully.")
    except SQLAlchemyError as e:
        print(f"❌ Error creating table: {e}")






def generate_columns_metadata_from_spark(df, primary_key=None, relationships=None):
    """
    Generates PostgreSQL-ready columns metadata from a Spark DataFrame schema.
    
    Args:
        df: Spark DataFrame
        primary_key (str): Name of the column to set as primary key
        relationships (dict): Optional. Relationship mappings:
            {
                "station_code": {"foreign_key": "stations.station_code"},
                "user_id": {"foreign_key": "users.id", "relation": "one-to-many"}
            }
    
    Returns:
        list: columns metadata
    """
    columns_metadata = []

    for field in df.schema.fields:
        dtype = field.dataType
        col_name = field.name
        col_meta = {
            "name": col_name,
            "nullable": field.nullable,
            "primary_key": (col_name == primary_key)
        }

        # Map Spark types → SQLAlchemy/Postgres types
        if isinstance(dtype, StringType):
            col_meta.update({"type": "String", "length": 255})
        elif isinstance(dtype, (IntegerType, LongType)):
            col_meta.update({"type": "Integer"})
        elif isinstance(dtype, (DoubleType, FloatType)):
            col_meta.update({"type": "Float"})
        elif isinstance(dtype, BooleanType):
            col_meta.update({"type": "Boolean"})
        elif isinstance(dtype, (TimestampType, DateType)):
            col_meta.update({"type": "DateTime"})
        elif isinstance(dtype, ArrayType):
            element_type = dtype.elementType
            if isinstance(element_type, IntegerType):
                col_meta.update({"type": "array", "element_type": "integer"})
            elif isinstance(element_type, StringType):
                col_meta.update({"type": "array", "element_type": "string"})
            else:
                raise ValueError(f"Unsupported Array element type: {element_type}")
        elif isinstance(dtype, (MapType, StructType)):
            col_meta.update({"type": "json"})  # Store as JSONB in PostgreSQL
        else:
            raise ValueError(f"Unsupported Spark type: {dtype}")

        # Handle relationships (foreign keys, one-to-many, etc.)
        if relationships and col_name in relationships:
            rel = relationships[col_name]
            if "foreign_key" in rel:
                col_meta["foreign_key"] = rel["foreign_key"]
            if "relation" in rel:
                col_meta["relation"] = rel["relation"]

        columns_metadata.append(col_meta)

    return columns_metadata
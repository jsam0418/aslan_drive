#!/usr/bin/env python3
"""
Schema Generator Tool for Aslan Drive

Generates Python dataclasses, SQLAlchemy models, and SQL migration scripts
from JSON schema definitions.
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load schema from JSON file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def python_type_mapping(json_type: str) -> str:
    """Map SQL types to Python import statements."""
    type_imports = {
        "datetime.date": "from datetime import date",
        "datetime.datetime": "from datetime import datetime",
        "Decimal": "from decimal import Decimal",
    }
    return type_imports.get(json_type, "")


def generate_dataclass(table_name: str, table_def: Dict[str, Any]) -> str:
    """Generate Python dataclass from table definition."""
    columns = table_def["columns"]

    # Collect imports
    imports = set(["from dataclasses import dataclass", "from typing import Optional"])
    for col_def in columns.values():
        py_type = col_def["python_type"]
        import_stmt = python_type_mapping(py_type)
        if import_stmt:
            imports.add(import_stmt)

    # Generate class
    class_name = "".join(word.capitalize() for word in table_name.split("_"))

    lines = []
    lines.extend(sorted(imports))
    lines.append("")
    lines.append("")
    lines.append("@dataclass")
    lines.append(f"class {class_name}:")
    lines.append(f'    """')
    lines.append(
        f'    {table_def.get("description", f"Data class for {table_name} table")}'
    )
    lines.append(f'    """')

    for col_name, col_def in columns.items():
        py_type = col_def["python_type"]
        if col_def.get("nullable", True) and not col_def.get("primary_key", False):
            py_type = f"Optional[{py_type}]"

        default_val = ""
        if col_def.get("nullable", True) and not col_def.get("primary_key", False):
            default_val = " = None"

        lines.append(
            f'    {col_name}: {py_type}{default_val}  # {col_def.get("description", "")}'
        )

    return "\n".join(lines)


def generate_sqlalchemy_model(table_name: str, table_def: Dict[str, Any]) -> str:
    """Generate SQLAlchemy model from table definition."""
    columns = table_def["columns"]

    class_name = "".join(word.capitalize() for word in table_name.split("_"))

    lines = []
    lines.append(
        "from sqlalchemy import Column, String, Date, DateTime, Numeric, BigInteger, Boolean"
    )
    lines.append("from sqlalchemy.ext.declarative import declarative_base")
    lines.append("from sqlalchemy.sql import func")
    lines.append("")
    lines.append("Base = declarative_base()")
    lines.append("")
    lines.append("")
    lines.append(f"class {class_name}(Base):")
    lines.append(f'    """')
    lines.append(
        f'    {table_def.get("description", f"SQLAlchemy model for {table_name} table")}'
    )
    lines.append(f'    """')
    lines.append(f'    __tablename__ = "{table_name}"')
    lines.append("")

    # Map SQL types to SQLAlchemy types
    sqlalchemy_type_map = {
        "VARCHAR": "String",
        "INTEGER": "BigInteger",
        "DATE": "Date",
        "TIMESTAMP WITH TIME ZONE": "DateTime",
        "DECIMAL": "Numeric",
        "BIGINT": "BigInteger",
        "BOOLEAN": "Boolean",
    }

    for col_name, col_def in columns.items():
        sql_type = col_def["type"]

        # Extract type and parameters
        if "(" in sql_type:
            base_type = sql_type.split("(")[0]
            params = sql_type.split("(")[1].rstrip(")")
        else:
            base_type = sql_type
            params = None

        sa_type = sqlalchemy_type_map.get(base_type, "String")

        # Build column definition
        col_parts = [f"Column({sa_type}"]
        if params and sa_type in ["String", "Numeric"]:
            if "," in params:
                col_parts[0] += f"({params})"
            else:
                col_parts[0] += f"({params})"

        if col_def.get("primary_key"):
            col_parts.append("primary_key=True")

        if not col_def.get("nullable", True):
            col_parts.append("nullable=False")

        if col_def.get("default") == "CURRENT_TIMESTAMP":
            col_parts.append("default=func.now()")
        elif col_def.get("default"):
            col_parts.append(f'default={col_def["default"]}')

        col_def_str = ", ".join(col_parts) + ")"

        lines.append(
            f'    {col_name} = {col_def_str}  # {col_def.get("description", "")}'
        )

    return "\n".join(lines)


def generate_sql_migration(schema: Dict[str, Any]) -> str:
    """Generate SQL migration script."""
    tables = schema["tables"]

    lines = []
    lines.append("-- Migration script generated from JSON schema")
    lines.append(f'-- Schema version: {schema.get("version", "unknown")}')
    lines.append(f"-- Generated at: {datetime.now().isoformat()}")
    lines.append("")

    for table_name, table_def in tables.items():
        lines.append(f"-- Create table: {table_name}")
        lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")

        columns = table_def["columns"]
        col_lines = []

        for col_name, col_def in columns.items():
            col_line = f'    {col_name} {col_def["type"]}'

            if not col_def.get("nullable", True):
                col_line += " NOT NULL"

            if col_def.get("default"):
                col_line += f' DEFAULT {col_def["default"]}'

            col_lines.append(col_line)

        # Add primary key constraint
        pk_cols = [name for name, defn in columns.items() if defn.get("primary_key")]
        if pk_cols:
            col_lines.append(f'    PRIMARY KEY ({", ".join(pk_cols)})')

        lines.append(",\n".join(col_lines))
        lines.append(");")
        lines.append("")

        # Create indexes
        for index in table_def.get("indexes", []):
            index_type = "UNIQUE INDEX" if index.get("unique") else "INDEX"
            cols_str = ", ".join(index["columns"])
            lines.append(
                f'CREATE {index_type} IF NOT EXISTS {index["name"]} ON {table_name} ({cols_str});'
            )

        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate code from JSON schema")
    parser.add_argument(
        "--schema", default="schemas/market_data.json", help="Path to JSON schema file"
    )
    parser.add_argument(
        "--output-dir", default="generated", help="Output directory for generated files"
    )

    args = parser.parse_args()

    # Load schema
    schema = load_schema(args.schema)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Generate files for each table
    for table_name, table_def in schema["tables"].items():
        # Generate dataclass
        dataclass_code = generate_dataclass(table_name, table_def)
        class_name = "".join(word.capitalize() for word in table_name.split("_"))

        with open(output_dir / f"{table_name}_dataclass.py", "w") as f:
            f.write(dataclass_code)

        # Generate SQLAlchemy model
        model_code = generate_sqlalchemy_model(table_name, table_def)
        with open(output_dir / f"{table_name}_model.py", "w") as f:
            f.write(model_code)

    # Generate SQL migration
    migration_sql = generate_sql_migration(schema)
    with open(output_dir / "migration.sql", "w") as f:
        f.write(migration_sql)

    # Generate combined models file
    all_imports = set()
    all_models = []

    for table_name, table_def in schema["tables"].items():
        model_code = generate_sqlalchemy_model(table_name, table_def)
        # Extract imports and model class
        lines = model_code.split("\n")
        imports = [line for line in lines if line.startswith(("from ", "import "))]
        all_imports.update(imports)

        # Find the class definition
        class_start = next(
            i for i, line in enumerate(lines) if line.startswith("class ")
        )
        model_class = "\n".join(lines[class_start:])
        all_models.append(model_class)

    combined_code = (
        "\n".join(sorted(all_imports))
        + "\n\nBase = declarative_base()\n\n"
        + "\n\n\n".join(all_models)
    )

    with open(output_dir / "models.py", "w") as f:
        f.write(combined_code)

    print(f"Generated code from {args.schema} to {args.output_dir}/")
    print(f"Files created:")
    print(f"  - models.py (combined SQLAlchemy models)")
    print(f"  - migration.sql (database migration script)")
    for table_name in schema["tables"].keys():
        print(f"  - {table_name}_dataclass.py")
        print(f"  - {table_name}_model.py")


if __name__ == "__main__":
    main()

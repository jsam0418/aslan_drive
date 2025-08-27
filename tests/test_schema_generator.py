"""
Tests for the schema generator tool
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.schema_generator import (
    load_schema, 
    generate_dataclass, 
    generate_sqlalchemy_model, 
    generate_sql_migration
)


@pytest.fixture
def sample_schema():
    """Sample schema for testing."""
    return {
        "version": "1.0.0",
        "tables": {
            "test_table": {
                "description": "Test table",
                "columns": {
                    "id": {
                        "type": "INTEGER",
                        "python_type": "int",
                        "primary_key": True,
                        "nullable": False
                    },
                    "name": {
                        "type": "VARCHAR(50)",
                        "python_type": "str",
                        "nullable": False
                    },
                    "price": {
                        "type": "DECIMAL(10,2)",
                        "python_type": "Decimal",
                        "nullable": True
                    }
                }
            }
        }
    }


def test_load_schema(sample_schema):
    """Test loading schema from JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_schema, f)
        schema_path = f.name
    
    try:
        loaded_schema = load_schema(schema_path)
        assert loaded_schema == sample_schema
    finally:
        Path(schema_path).unlink()


def test_generate_dataclass(sample_schema):
    """Test dataclass generation."""
    table_def = sample_schema["tables"]["test_table"]
    result = generate_dataclass("test_table", table_def)
    
    assert "class TestTable:" in result
    assert "id: int" in result
    assert "name: str" in result
    assert "price: Optional[Decimal] = None" in result
    assert "from decimal import Decimal" in result
    assert "@dataclass" in result


def test_generate_sqlalchemy_model(sample_schema):
    """Test SQLAlchemy model generation."""
    table_def = sample_schema["tables"]["test_table"]
    result = generate_sqlalchemy_model("test_table", table_def)
    
    assert "class TestTable(Base):" in result
    assert "__tablename__ = \"test_table\"" in result
    assert "Column(BigInteger, primary_key=True)" in result
    assert "Column(String(50), nullable=False)" in result


def test_generate_sql_migration(sample_schema):
    """Test SQL migration generation."""
    result = generate_sql_migration(sample_schema)
    
    assert "CREATE TABLE IF NOT EXISTS test_table" in result
    assert "id INTEGER" in result
    assert "name VARCHAR(50)" in result
    assert "price DECIMAL(10,2)" in result
    assert "PRIMARY KEY" in result
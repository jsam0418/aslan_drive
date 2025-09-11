#!/usr/bin/env python3
"""
Basic functionality test that doesn't require external dependencies
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that basic imports work"""
    try:
        from models import Base, DailyOHLCV, Symbol
        from services.data_ingestion.mock_data_generator import MockOHLCVGenerator
        from services.data_ingestion.database import DatabaseManager
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_sqlalchemy_models():
    """Test SQLAlchemy models"""
    try:
        from models import Base, DailyOHLCV, Symbol
        from sqlalchemy import create_engine
        
        # Test model instantiation
        symbol = Symbol(
            symbol="TEST",
            name="Test Symbol",
            asset_class="equity",
            currency="USD",
            active=True
        )
        
        # Test that models have correct attributes
        assert hasattr(DailyOHLCV, '__tablename__')
        assert hasattr(Symbol, '__tablename__')
        assert DailyOHLCV.__tablename__ == 'daily_ohlcv'
        assert Symbol.__tablename__ == 'symbols'
        
        # Test that we can create an in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        
        print("✅ SQLAlchemy models work")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy models failed: {e}")
        return False

def test_mock_generator():
    """Test mock data generator"""
    try:
        from services.data_ingestion.mock_data_generator import MockOHLCVGenerator
        generator = MockOHLCVGenerator()
        assert len(generator.symbols) > 0
        assert "AAPL" in generator.symbols
        print("✅ Mock data generator works")
        return True
    except Exception as e:
        print(f"❌ Mock data generator failed: {e}")
        return False

def test_alembic_config():
    """Test Alembic configuration"""
    try:
        from pathlib import Path
        
        # Check that alembic.ini exists
        alembic_ini = Path("alembic.ini")
        assert alembic_ini.exists(), "alembic.ini not found"
        
        # Check that alembic directory exists
        alembic_dir = Path("alembic")
        assert alembic_dir.exists(), "alembic directory not found"
        
        # Check that migrations directory exists
        versions_dir = Path("alembic/versions")
        assert versions_dir.exists(), "alembic/versions directory not found"
        
        # Check that there's at least one migration file
        migration_files = list(versions_dir.glob("*.py"))
        assert len(migration_files) > 0, "No migration files found"
        
        print("✅ Alembic configuration works")
        return True
    except Exception as e:
        print(f"❌ Alembic configuration failed: {e}")
        return False

def main():
    """Run basic tests"""
    print("🧪 Running basic functionality tests...")
    
    tests = [
        test_imports,
        test_sqlalchemy_models,
        test_mock_generator,
        test_alembic_config,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
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
        from tools.schema_generator import load_schema, generate_dataclass
        from services.data_ingestion.mock_data_generator import MockOHLCVGenerator
        print("✅ Basic imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_schema_generator():
    """Test schema generator"""
    try:
        from tools.schema_generator import load_schema
        schema = load_schema("schemas/market_data.json")
        assert "tables" in schema
        assert "daily_ohlcv" in schema["tables"]
        print("✅ Schema generator works")
        return True
    except Exception as e:
        print(f"❌ Schema generator failed: {e}")
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

def main():
    """Run basic tests"""
    print("🧪 Running basic functionality tests...")
    
    tests = [
        test_imports,
        test_schema_generator,
        test_mock_generator,
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
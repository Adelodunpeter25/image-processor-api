"""Run all tests."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def run_all_tests():
    """Run all test modules."""
    print("=" * 60)
    print("Running Image Processor Tests")
    print("=" * 60)
    
    tests = [
        ('Thumbnail Generation', 'test_thumbnail'),
        ('Background Removal', 'test_bg_removal'),
        ('Batch Processing', 'test_batch_processing'),
        ('Supabase Upload', 'test_supabase_upload'),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_module in tests:
        print(f"\n{'=' * 60}")
        print(f"Test: {test_name}")
        print('=' * 60)
        
        try:
            module = __import__(test_module)
            if test_module == 'test_thumbnail':
                module.test_thumbnail_generation()
            elif test_module == 'test_bg_removal':
                module.test_background_removal()
            elif test_module == 'test_batch_processing':
                module.test_batch_transform()
                module.test_batch_background_removal()
                module.test_batch_zip_creation()
            elif test_module == 'test_supabase_upload':
                module.test_supabase_upload()
            
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {str(e)}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print('=' * 60)
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Tests

This directory contains tests for the Image Processor API.

## Test Files

- `test_thumbnail.py` - Tests thumbnail generation with various sizes
- `test_bg_removal.py` - Tests AI-powered background removal
- `test_batch_processing.py` - Tests batch transformation, background removal, and ZIP creation
- `test_supabase_upload.py` - Tests Supabase storage upload functionality

## Running Tests

### Run all tests:
```bash
cd tests
python run_tests.py
```

### Run individual tests:
```bash
# Test thumbnail generation
python test_thumbnail.py

# Test background removal
python test_bg_removal.py

# Test batch processing
python test_batch_processing.py

# Test Supabase upload (requires production env vars)
python test_supabase_upload.py
```

## Requirements

Make sure you have all dependencies installed:
```bash
pip install -r ../requirements.txt
```

## Notes

- **Supabase test** requires valid `PROJECT_URL`, `SERVICE_ROLE`, and `SUPABASE_BUCKET` in `.env`
- **Background removal test** will download the AI model on first run (~176MB)
- **Batch processing test** creates multiple images and tests ZIP file creation
- Tests create temporary images in memory and clean up after themselves

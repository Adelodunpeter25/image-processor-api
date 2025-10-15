"""Initialize database tables."""
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from main import app
from models.user import db
from models.api_key import APIKey
from models.preset import Preset
from models.image import Image

print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

with app.app_context():
    print("\nCreating database tables...")
    
    try:
        # Test connection
        db.engine.connect()
        print("✅ Database connection successful!")
        
        # Create all tables
        db.create_all()
        print("✅ All tables created successfully!")
        
        # Verify tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\nTables in database: {tables}")
        print("\nExpected tables:")
        print("  - user")
        print("  - image")
        print("  - api_keys")
        print("  - presets")
        
    except Exception as e:
        print(f"❌ Error: {e}")

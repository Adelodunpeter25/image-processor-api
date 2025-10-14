"""Create presets table in database."""
from main import app, db
from models.preset import Preset

with app.app_context():
    db.create_all()
    print("✓ Presets table created successfully!")

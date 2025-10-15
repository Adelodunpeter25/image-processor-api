"""Seed database with popular preset transformations."""
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from main import app, db
from models.preset import Preset
from models.user import User

# Popular social media presets
POPULAR_PRESETS = [
    {
        'name': 'Instagram Square',
        'description': 'Perfect square for Instagram posts (1080x1080)',
        'width': 1080,
        'height': 1080,
        'format': 'jpeg',
        'quality': 90,
        'is_public': True
    },
    {
        'name': 'Instagram Story',
        'description': 'Vertical format for Instagram stories (1080x1920)',
        'width': 1080,
        'height': 1920,
        'format': 'jpeg',
        'quality': 90,
        'is_public': True
    },
    {
        'name': 'Twitter Header',
        'description': 'Twitter/X header image (1500x500)',
        'width': 1500,
        'height': 500,
        'format': 'jpeg',
        'quality': 85,
        'is_public': True
    },
    {
        'name': 'Facebook Cover',
        'description': 'Facebook cover photo (820x312)',
        'width': 820,
        'height': 312,
        'format': 'jpeg',
        'quality': 85,
        'is_public': True
    },
    {
        'name': 'LinkedIn Banner',
        'description': 'LinkedIn profile banner (1584x396)',
        'width': 1584,
        'height': 396,
        'format': 'jpeg',
        'quality': 85,
        'is_public': True
    },
    {
        'name': 'YouTube Thumbnail',
        'description': 'YouTube video thumbnail (1280x720)',
        'width': 1280,
        'height': 720,
        'format': 'jpeg',
        'quality': 90,
        'is_public': True
    },
    {
        'name': 'Web Optimized',
        'description': 'Optimized for web with compression',
        'width': 1200,
        'format': 'webp',
        'quality': 80,
        'optimize': True,
        'compress': True,
        'is_public': True
    },
    {
        'name': 'Thumbnail Small',
        'description': 'Small thumbnail (300x300)',
        'width': 300,
        'height': 300,
        'format': 'jpeg',
        'quality': 85,
        'is_public': True
    },
    {
        'name': 'Profile Picture',
        'description': 'Standard profile picture (400x400)',
        'width': 400,
        'height': 400,
        'format': 'jpeg',
        'quality': 90,
        'is_public': True
    },
    {
        'name': 'Email Signature',
        'description': 'Small image for email signatures (200x200)',
        'width': 200,
        'height': 200,
        'format': 'png',
        'quality': 90,
        'is_public': True
    }
]

with app.app_context():
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Get first user (or create a system user)
    user = User.query.first()
    
    if not user:
        print("No users found. Creating system user...")
        user = User(email='system@imageprocessor.com')
        user.set_password('system_password_change_me')
        db.session.add(user)
        db.session.commit()
    
    # Create presets
    for preset_data in POPULAR_PRESETS:
        existing = Preset.query.filter_by(name=preset_data['name'], user_id=user.id).first()
        
        if not existing:
            preset = Preset(
                user_id=user.id,
                **preset_data
            )
            db.session.add(preset)
            print(f"✓ Created preset: {preset_data['name']}")
        else:
            print(f"- Preset already exists: {preset_data['name']}")
    
    db.session.commit()
    print(f"\n✓ Seeded {len(POPULAR_PRESETS)} popular presets!")

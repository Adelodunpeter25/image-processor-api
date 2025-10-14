"""Image model for storing image metadata."""
from models.user import db
from datetime import datetime

class Image(db.Model):
    """Image model with metadata and user relationship."""
    __tablename__ = 'images'
    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    format = db.Column(db.String(10), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # File size in bytes
    width = db.Column(db.Integer, nullable=False)  # Image width in pixels
    height = db.Column(db.Integer, nullable=False)  # Image height in pixels
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

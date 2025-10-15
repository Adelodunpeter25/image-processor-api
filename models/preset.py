"""Preset model for storing transformation presets."""
from models.user import db
from datetime import datetime

class Preset(db.Model):
    """Preset model for reusable transformations."""
    
    __tablename__ = 'presets'
    __table_args__ = (
        db.Index('idx_user_name', 'user_id', 'name'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)  # Public presets can be used by anyone
    
    # Transformation parameters stored as JSON
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    format = db.Column(db.String(10))
    quality = db.Column(db.Integer)
    crop_x = db.Column(db.Integer)
    crop_y = db.Column(db.Integer)
    crop_width = db.Column(db.Integer)
    crop_height = db.Column(db.Integer)
    rotate = db.Column(db.Integer)
    watermark = db.Column(db.String(255))
    optimize = db.Column(db.Boolean, default=False)
    enhance = db.Column(db.Boolean, default=False)
    compress = db.Column(db.Boolean, default=False)
    grayscale = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """Convert preset to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_public': self.is_public,
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'quality': self.quality,
            'crop_x': self.crop_x,
            'crop_y': self.crop_y,
            'crop_width': self.crop_width,
            'crop_height': self.crop_height,
            'rotate': self.rotate,
            'watermark': self.watermark,
            'optimize': self.optimize,
            'enhance': self.enhance,
            'compress': self.compress,
            'grayscale': self.grayscale,
            'created_at': self.created_at.isoformat(),
            'usage_count': self.usage_count
        }
    
    def get_params(self):
        """Get transformation parameters as dict."""
        return {
            'width': self.width,
            'height': self.height,
            'format': self.format,
            'quality': self.quality,
            'crop_x': self.crop_x,
            'crop_y': self.crop_y,
            'crop_width': self.crop_width,
            'crop_height': self.crop_height,
            'rotate': self.rotate,
            'watermark_text': self.watermark,
            'optimize': self.optimize,
            'enhance': self.enhance,
            'compress': self.compress,
            'grayscale': self.grayscale
        }

"""API Key model for programmatic access."""
from models.user import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class APIKey(db.Model):
    """API Key model for user authentication."""
    
    __tablename__ = 'api_keys'
    __table_args__ = (
        db.Index('idx_prefix_active', 'prefix', 'is_active'),
        db.Index('idx_user_active', 'user_id', 'is_active'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False)
    prefix = db.Column(db.String(20), nullable=True)  # Optional for display
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    request_count = db.Column(db.Integer, default=0)  # Track total requests
    
    def __repr__(self):
        return f'<APIKey {self.name} - {self.prefix}>'
    
    def set_key(self, key):
        """Hash and store the API key."""
        self.key_hash = generate_password_hash(key)
    
    def check_key(self, key):
        """Verify API key."""
        return check_password_hash(self.key_hash, key)
    
    def increment_usage(self):
        """Increment request count and update last used."""
        self.request_count += 1
        self.last_used = datetime.utcnow()

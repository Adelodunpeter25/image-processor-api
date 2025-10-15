"""Info endpoint for API usage metrics."""
from flask import Blueprint, jsonify, render_template_string
from models.user import db, User
from models.image import Image
from models.api_key import APIKey
from models.preset import Preset
from sqlalchemy import func
import os
from datetime import datetime

info_bp = Blueprint('info', __name__)

# Track service start time
SERVICE_START_TIME = datetime.utcnow()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>API Metrics Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { 
            color: white; 
            text-align: center; 
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px;
            margin-bottom: 20px;
        }
        .card { 
            background: #16213e; 
            border-radius: 12px; 
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 1px solid #0f3460;
        }
        .card h2 { 
            color: #00d4ff; 
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #0f3460;
            padding-bottom: 10px;
        }
        .stat { 
            display: flex; 
            justify-content: space-between; 
            padding: 10px 0;
            border-bottom: 1px solid #0f3460;
        }
        .stat:last-child { border-bottom: none; }
        .stat-label { color: #a8b2d1; font-weight: 500; }
        .stat-value { 
            color: #e6f1ff; 
            font-weight: bold;
            background: #0f3460;
            padding: 4px 12px;
            border-radius: 6px;
        }
        .status-healthy { color: #00ff88; font-weight: bold; }
        .preset-item, .format-item {
            padding: 8px 0;
            border-bottom: 1px solid #0f3460;
            color: #a8b2d1;
        }
        .preset-item:last-child, .format-item:last-child { border-bottom: none; }
        .badge { 
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-left: 8px;
        }
        .badge-public { background: #00ff88; color: #1a1a2e; }
        .badge-private { background: #6c757d; color: white; }
        small { color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 API Metrics Dashboard</h1>
        
        <div class="grid">
            <div class="card">
                <h2>📈 API Statistics</h2>
                <div class="stat">
                    <span class="stat-label">Total Users</span>
                    <span class="stat-value">{{ data.api_stats.total_users }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Images</span>
                    <span class="stat-value">{{ data.api_stats.total_images }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Active API Keys</span>
                    <span class="stat-value">{{ data.api_stats.total_api_keys }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total Presets</span>
                    <span class="stat-value">{{ data.api_stats.total_presets }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Public Presets</span>
                    <span class="stat-value">{{ data.api_stats.public_presets }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Total API Requests</span>
                    <span class="stat-value">{{ data.api_stats.total_api_requests }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Avg Images/User</span>
                    <span class="stat-value">{{ data.api_stats.average_images_per_user }}</span>
                </div>
            </div>

            <div class="card">
                <h2>💾 Storage Metrics</h2>
                <div class="stat">
                    <span class="stat-label">Total Storage</span>
                    <span class="stat-value">{{ data.storage_metrics.total_storage_mb }} MB</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Average Image Size</span>
                    <span class="stat-value">{{ data.storage_metrics.average_image_size_kb }} KB</span>
                </div>
            </div>

            <div class="card">
                <h2>🎨 Format Statistics</h2>
                <div class="stat">
                    <span class="stat-label">Most Popular</span>
                    <span class="stat-value">{{ data.format_stats.most_popular_format or 'N/A' }}</span>
                </div>
                {% for fmt in data.format_stats.format_distribution %}
                <div class="format-item">
                    <span class="stat-label">{{ fmt.format.upper() }}</span>
                    <span class="stat-value">{{ fmt.count }}</span>
                </div>
                {% endfor %}
            </div>

            <div class="card">
                <h2>⚡ API Health</h2>
                <div class="stat">
                    <span class="stat-label">Status</span>
                    <span class="stat-value status-healthy">{{ data.api_health.status.upper() }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Environment</span>
                    <span class="stat-value">{{ data.api_health.environment }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Uptime</span>
                    <span class="stat-value">{{ data.api_health.uptime_days }} days</span>
                </div>
            </div>

            <div class="card">
                <h2>⚙️ Configuration</h2>
                <div class="stat">
                    <span class="stat-label">Version</span>
                    <span class="stat-value">{{ data.api_configuration.version }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Max File Size</span>
                    <span class="stat-value">{{ data.api_configuration.max_file_size_mb }} MB</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Rate Limit</span>
                    <span class="stat-value">{{ data.api_configuration.rate_limit }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Storage</span>
                    <span class="stat-value">{{ data.api_configuration.storage_backend }}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Formats</span>
                    <span class="stat-value">{{ data.api_configuration.supported_formats|join(', ') }}</span>
                </div>
            </div>

            <div class="card">
                <h2>🔥 Most Used Presets</h2>
                {% if data.most_used_presets %}
                    {% for preset in data.most_used_presets %}
                    <div class="preset-item">
                        <strong>{{ preset.name }}</strong>
                        <span class="badge {% if preset.is_public %}badge-public{% else %}badge-private{% endif %}">
                            {% if preset.is_public %}Public{% else %}Private{% endif %}
                        </span>
                        <br>
                        <small style="color: #666;">Used {{ preset.usage_count }} times</small>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: #666; text-align: center;">No presets used yet</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

@info_bp.route('', methods=['GET'])
def api_info():
    """Get API usage metrics dashboard."""
    try:
        from main import app
        
        # Global stats
        total_users = User.query.count()
        total_images = Image.query.count()
        total_api_keys = APIKey.query.filter_by(is_active=True).count()
        total_presets = Preset.query.count()
        public_presets = Preset.query.filter_by(is_public=True).count()
        
        # Total API requests across all keys
        total_requests = db.session.query(func.sum(APIKey.request_count)).scalar() or 0
        
        # Storage metrics
        total_storage = db.session.query(func.sum(Image.size)).scalar() or 0
        avg_image_size = db.session.query(func.avg(Image.size)).scalar() or 0
        
        # Most popular format
        popular_format = db.session.query(
            Image.format,
            func.count(Image.id).label('count')
        ).group_by(Image.format).order_by(func.count(Image.id).desc()).first()
        
        # Format distribution
        format_stats = db.session.query(
            Image.format,
            func.count(Image.id).label('count')
        ).group_by(Image.format).all()
        
        # Most used presets
        top_presets = Preset.query.filter(
            Preset.usage_count > 0
        ).order_by(Preset.usage_count.desc()).limit(5).all()
        
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - SERVICE_START_TIME).total_seconds()
        uptime_hours = uptime_seconds / 3600
        
        # API configuration
        env = os.getenv('FLASK_ENV', 'development')
        
        data = {
            'api_stats': {
                'total_users': total_users,
                'total_images': total_images,
                'total_api_keys': total_api_keys,
                'total_presets': total_presets,
                'public_presets': public_presets,
                'total_api_requests': int(total_requests),
                'average_images_per_user': round(total_images / total_users, 2) if total_users > 0 else 0
            },
            'storage_metrics': {
                'total_storage_bytes': int(total_storage),
                'total_storage_mb': round(total_storage / (1024 * 1024), 2),
                'average_image_size_bytes': int(avg_image_size),
                'average_image_size_kb': round(avg_image_size / 1024, 2)
            },
            'format_stats': {
                'most_popular_format': popular_format[0] if popular_format else None,
                'format_distribution': [
                    {'format': fmt, 'count': count} 
                    for fmt, count in format_stats
                ]
            },
            'most_used_presets': [
                {
                    'id': preset.id,
                    'name': preset.name,
                    'usage_count': preset.usage_count,
                    'is_public': preset.is_public
                }
                for preset in top_presets
            ],
            'api_health': {
                'status': 'healthy',
                'environment': env,
                'uptime_hours': round(uptime_hours, 2),
                'uptime_days': round(uptime_hours / 24, 2)
            },
            'api_configuration': {
                'version': '1.0.0',
                'max_file_size_mb': app.config.get('MAX_CONTENT_LENGTH', 0) / (1024 * 1024),
                'supported_formats': list(app.config.get('ALLOWED_EXTENSIONS', [])),
                'rate_limit': '20 requests per minute',
                'storage_backend': 'Supabase' if env == 'production' else 'Local'
            }
        }
        
        return render_template_string(HTML_TEMPLATE, data=data)
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch metrics', 'message': str(e)}), 500

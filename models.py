from app import db
from datetime import datetime
import json

class SavedProgression(db.Model):
    __tablename__ = 'saved_progressions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    key_signature = db.Column(db.String(10), nullable=False)
    scale_type = db.Column(db.String(20), nullable=False)
    style = db.Column(db.String(20), nullable=False)
    rhythm = db.Column(db.String(20), nullable=False)
    
    # Store chord progression as JSON
    chords_data = db.Column(db.Text, nullable=False)
    scale_notes = db.Column(db.Text, nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    times_generated = db.Column(db.Integer, default=1)
    is_favorite = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'key_signature': self.key_signature,
            'scale_type': self.scale_type,
            'style': self.style,
            'rhythm': self.rhythm,
            'chords_data': json.loads(self.chords_data),
            'scale_notes': json.loads(self.scale_notes),
            'created_at': self.created_at.isoformat(),
            'times_generated': self.times_generated,
            'is_favorite': self.is_favorite
        }
    
    def set_chords_data(self, chords_list):
        self.chords_data = json.dumps(chords_list)
    
    def set_scale_notes(self, notes_list):
        self.scale_notes = json.dumps(notes_list)

class UserStatistics(db.Model):
    __tablename__ = 'user_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    total_progressions_generated = db.Column(db.Integer, default=0)
    most_used_key = db.Column(db.String(10))
    most_used_scale = db.Column(db.String(20))
    most_used_style = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'total_progressions_generated': self.total_progressions_generated,
            'most_used_key': self.most_used_key,
            'most_used_scale': self.most_used_scale,
            'most_used_style': self.most_used_style,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
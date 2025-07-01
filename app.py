import os
import random
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.colors import black, blue, gray

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

# Musical theory constants
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Scale intervals (semitones from root)
SCALE_INTERVALS = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'locrian': [0, 1, 3, 5, 6, 8, 10],
    'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
    'melodic_minor': [0, 2, 3, 5, 7, 9, 11]
}

# Scale display names
SCALE_NAMES = {
    'major': 'Maggiore',
    'minor': 'Minore Naturale',
    'dorian': 'Dorico',
    'phrygian': 'Frigio',
    'lydian': 'Lidio',
    'mixolydian': 'Misolidio',
    'locrian': 'Locrio',
    'harmonic_minor': 'Minore Armonico',
    'melodic_minor': 'Minore Melodico'
}

# Enhanced chord degrees and types for different scales with extended chords
DEGREE_MAPPINGS = {
    'major': {
        'degrees': {'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'V': 4, 'vi': 5, 'vii°': 6, 'I7': 0, 'ii7': 1, 'iii7': 2, 'IV7': 3, 'V7': 4, 'vi7': 5, 'I9': 0, 'V9': 4, 'Isus2': 0, 'Isus4': 0, 'Vsus4': 4},
        'types': {'I': 'maj', 'ii': 'min', 'iii': 'min', 'IV': 'maj', 'V': 'maj', 'vi': 'min', 'vii°': 'dim', 'I7': 'maj7', 'ii7': 'm7', 'iii7': 'm7', 'IV7': 'maj7', 'V7': '7', 'vi7': 'm7', 'I9': '9', 'V9': '9', 'Isus2': 'sus2', 'Isus4': 'sus4', 'Vsus4': 'sus4'}
    },
    'minor': {
        'degrees': {'i': 0, 'ii°': 1, 'bIII': 2, 'iv': 3, 'v': 4, 'bVI': 5, 'bVII': 6, 'i7': 0, 'ii°7': 1, 'bIII7': 2, 'iv7': 3, 'v7': 4, 'bVI7': 5, 'bVII7': 6, 'i9': 0, 'isus2': 0, 'isus4': 0},
        'types': {'i': 'min', 'ii°': 'dim', 'bIII': 'maj', 'iv': 'min', 'v': 'min', 'bVI': 'maj', 'bVII': 'maj', 'i7': 'm7', 'ii°7': 'dim', 'bIII7': 'maj7', 'iv7': 'm7', 'v7': 'm7', 'bVI7': 'maj7', 'bVII7': '7', 'i9': '9', 'isus2': 'sus2', 'isus4': 'sus4'}
    },
    'dorian': {
        'degrees': {'i': 0, 'ii': 1, 'bIII': 2, 'IV': 3, 'v': 4, 'vi°': 5, 'bVII': 6, 'i7': 0, 'ii7': 1, 'bIII7': 2, 'IV7': 3, 'v7': 4, 'bVII7': 6, 'isus2': 0, 'isus4': 0, 'IVsus2': 3},
        'types': {'i': 'min', 'ii': 'min', 'bIII': 'maj', 'IV': 'maj', 'v': 'min', 'vi°': 'dim', 'bVII': 'maj', 'i7': 'm7', 'ii7': 'm7', 'bIII7': 'maj7', 'IV7': 'maj7', 'v7': 'm7', 'bVII7': '7', 'isus2': 'sus2', 'isus4': 'sus4', 'IVsus2': 'sus2'}
    },
    'phrygian': {
        'degrees': {'i': 0, 'bII': 1, 'bIII': 2, 'iv': 3, 'v°': 4, 'bVI': 5, 'bvii': 6, 'i7': 0, 'bII7': 1, 'bIII7': 2, 'iv7': 3, 'bVI7': 5, 'bvii7': 6, 'isus2': 0, 'bIIsus2': 1},
        'types': {'i': 'min', 'bII': 'maj', 'bIII': 'maj', 'iv': 'min', 'v°': 'dim', 'bVI': 'maj', 'bvii': 'min', 'i7': 'm7', 'bII7': 'maj7', 'bIII7': 'maj7', 'iv7': 'm7', 'bVI7': 'maj7', 'bvii7': 'm7', 'isus2': 'sus2', 'bIIsus2': 'sus2'}
    },
    'lydian': {
        'degrees': {'I': 0, 'II': 1, 'iii': 2, '#iv°': 3, 'V': 4, 'vi': 5, 'vii': 6, 'I7': 0, 'II7': 1, 'iii7': 2, 'V7': 4, 'vi7': 5, 'vii7': 6, 'I9': 0, 'Isus2': 0, 'IIsus4': 1},
        'types': {'I': 'maj', 'II': 'maj', 'iii': 'min', '#iv°': 'dim', 'V': 'maj', 'vi': 'min', 'vii': 'min', 'I7': 'maj7', 'II7': '7', 'iii7': 'm7', 'V7': '7', 'vi7': 'm7', 'vii7': 'm7', 'I9': '9', 'Isus2': 'sus2', 'IIsus4': 'sus4'}
    },
    'mixolydian': {
        'degrees': {'I': 0, 'ii': 1, 'iii°': 2, 'IV': 3, 'v': 4, 'vi': 5, 'bVII': 6, 'I7': 0, 'ii7': 1, 'IV7': 3, 'v7': 4, 'vi7': 5, 'bVII7': 6, 'I9': 0, 'Isus4': 0, 'bVIIsus2': 6},
        'types': {'I': 'maj', 'ii': 'min', 'iii°': 'dim', 'IV': 'maj', 'v': 'min', 'vi': 'min', 'bVII': 'maj', 'I7': '7', 'ii7': 'm7', 'IV7': 'maj7', 'v7': 'm7', 'vi7': 'm7', 'bVII7': 'maj7', 'I9': '9', 'Isus4': 'sus4', 'bVIIsus2': 'sus2'}
    },
    'locrian': {
        'degrees': {'i°': 0, 'bII': 1, 'biii': 2, 'iv': 3, 'bV': 4, 'bVI': 5, 'bvii': 6, 'i°7': 0, 'bII7': 1, 'biii7': 2, 'iv7': 3, 'bV7': 4, 'bVI7': 5, 'bvii7': 6, 'bIIsus2': 1, 'ivsus4': 3},
        'types': {'i°': 'dim', 'bII': 'maj', 'biii': 'min', 'iv': 'min', 'bV': 'maj', 'bVI': 'maj', 'bvii': 'min', 'i°7': 'dim', 'bII7': 'maj7', 'biii7': 'm7', 'iv7': 'm7', 'bV7': 'maj7', 'bVI7': 'maj7', 'bvii7': 'm7', 'bIIsus2': 'sus2', 'ivsus4': 'sus4'}
    },
    'harmonic_minor': {
        'degrees': {'i': 0, 'ii°': 1, 'bIII+': 2, 'iv': 3, 'V': 4, 'bVI': 5, 'vii°': 6, 'i7': 0, 'ii°7': 1, 'bIII+7': 2, 'iv7': 3, 'V7': 4, 'bVI7': 5, 'vii°7': 6, 'i9': 0, 'V9': 4, 'isus2': 0, 'Vsus4': 4},
        'types': {'i': 'min', 'ii°': 'dim', 'bIII+': 'aug', 'iv': 'min', 'V': 'maj', 'bVI': 'maj', 'vii°': 'dim', 'i7': 'm7', 'ii°7': 'dim', 'bIII+7': 'aug', 'iv7': 'm7', 'V7': '7', 'bVI7': 'maj7', 'vii°7': 'dim', 'i9': '9', 'V9': '9', 'isus2': 'sus2', 'Vsus4': 'sus4'}
    },
    'melodic_minor': {
        'degrees': {'i': 0, 'ii': 1, 'bIII+': 2, 'IV': 3, 'V': 4, 'vi°': 5, 'vii°': 6, 'i7': 0, 'ii7': 1, 'bIII+7': 2, 'IV7': 3, 'V7': 4, 'vi°7': 5, 'vii°7': 6, 'i9': 0, 'V9': 4, 'isus2': 0, 'IVsus2': 3},
        'types': {'i': 'min', 'ii': 'min', 'bIII+': 'aug', 'IV': 'maj', 'V': 'maj', 'vi°': 'dim', 'vii°': 'dim', 'i7': 'm7', 'ii7': 'm7', 'bIII+7': 'aug', 'IV7': 'maj7', 'V7': '7', 'vi°7': 'dim', 'vii°7': 'dim', 'i9': '9', 'V9': '9', 'isus2': 'sus2', 'IVsus2': 'sus2'}
    }
}

# Enhanced chord progressions with extended chords
PROGRESSIONI = {
    "pop": {
        "major": ["I", "vi", "IV", "V", "ii", "V7", "Isus4", "Vsus4", "vi7", "I9"],
        "minor": ["i", "bVII", "bVI", "iv", "v", "i7", "V7", "isus2", "bVII7", "iv7"],
        "dorian": ["i", "ii", "bVII", "IV", "v", "i7", "ii7", "bVII7", "isus4", "IVsus2"],
        "phrygian": ["i", "bII", "bVII", "iv", "bIII", "i7", "bII7", "isus2", "bIIsus2", "iv7"],
        "lydian": ["I", "II", "V", "vi", "iii", "I7", "II7", "I9", "Isus2", "IIsus4"],
        "mixolydian": ["I", "bVII", "IV", "v", "ii", "I7", "I9", "Isus4", "bVIIsus2", "iv7"],
        "locrian": ["i°", "bII", "bV", "iv", "bVI", "i°7", "bII7", "bIIsus2", "ivsus4", "bVI7"],
        "harmonic_minor": ["i", "V", "bVI", "iv", "vii°", "i7", "V7", "V9", "isus2", "Vsus4"],
        "melodic_minor": ["i", "V", "IV", "ii", "bIII+", "i7", "V7", "IV7", "isus2", "IVsus2"]
    },
    "rock": {
        "major": ["I", "bVII", "IV", "V", "vi", "V7", "Isus4", "Vsus4", "vii°", "IV7"],
        "minor": ["i", "bVII", "bVI", "iv", "bIII", "i7", "bVII7", "v7", "ii°", "isus4"],
        "dorian": ["i", "bVII", "IV", "ii", "v", "i7", "bVII7", "IV7", "ii7", "isus4"],
        "phrygian": ["i", "bII", "bVII", "bIII", "iv", "i7", "bII7", "bIII7", "isus2", "iv7"],
        "lydian": ["I", "II", "V", "#iv°", "vi", "I7", "II7", "V7", "Isus2", "vi7"],
        "mixolydian": ["I", "bVII", "IV", "v", "vi", "I7", "bVII7", "IV7", "Isus4", "v7"],
        "locrian": ["i°", "bII", "bV", "bVI", "bvii", "i°7", "bII7", "bV7", "bIIsus2", "bvii7"],
        "harmonic_minor": ["i", "V", "bVI", "vii°", "iv", "i7", "V7", "bVI7", "vii°7", "Vsus4"],
        "melodic_minor": ["i", "V", "IV", "V", "ii", "i7", "V7", "IV7", "ii7", "isus2"]
    },
    "jazz": {
        "major": ["Imaj7", "ii7", "V7", "vi7", "IV7", "I9", "V9", "iii7", "vii°7", "Isus4"],
        "minor": ["i7", "iv7", "bVII7", "bIII7", "bVI7", "i9", "V7", "ii°7", "isus2", "iv9"],
        "dorian": ["i7", "ii7", "bVII7", "IV7", "v7", "i9", "bVII9", "isus2", "isus4", "IVsus2"],
        "phrygian": ["i7", "bII7", "bVI7", "iv7", "biii7", "isus2", "bIIsus2", "i9", "bII9", "iv9"],
        "lydian": ["I7", "II7", "v7", "vi7", "iii7", "I9", "Isus2", "IIsus4", "V7", "vi9"],
        "mixolydian": ["I7", "bVII7", "IV7", "v7", "ii7", "I9", "Isus4", "bVIIsus2", "v9", "IV9"],
        "locrian": ["i°7", "bII7", "bV7", "bVI7", "bvii7", "bIIsus2", "ivsus4", "bII9", "bV9", "iv7"],
        "harmonic_minor": ["i7", "V7", "bVI7", "iv7", "vii°7", "i9", "V9", "isus2", "Vsus4", "bVI9"],
        "melodic_minor": ["i7", "V7", "IV7", "ii7", "bIII+7", "i9", "V9", "isus2", "IVsus2", "ii9"]
    }
}

# Comprehensive guitar tablatures database
TABLATURES = {
    # Major chords
    'C maj': ['e|--0--', 'B|--1--', 'G|--0--', 'D|--2--', 'A|--3--', 'E|--x--'],
    'C# maj': ['e|--4--', 'B|--6--', 'G|--6--', 'D|--6--', 'A|--4--', 'E|--x--'],
    'Db maj': ['e|--4--', 'B|--6--', 'G|--6--', 'D|--6--', 'A|--4--', 'E|--x--'],
    'D maj': ['e|--2--', 'B|--3--', 'G|--2--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'D# maj': ['e|--3--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb maj': ['e|--3--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'E maj': ['e|--0--', 'B|--0--', 'G|--1--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'F maj': ['e|--1--', 'B|--1--', 'G|--2--', 'D|--3--', 'A|--3--', 'E|--1--'],
    'F# maj': ['e|--2--', 'B|--2--', 'G|--3--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'Gb maj': ['e|--2--', 'B|--2--', 'G|--3--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'G maj': ['e|--3--', 'B|--0--', 'G|--0--', 'D|--0--', 'A|--2--', 'E|--3--'],
    'G# maj': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--6--', 'A|--6--', 'E|--4--'],
    'Ab maj': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--6--', 'A|--6--', 'E|--4--'],
    'A maj': ['e|--0--', 'B|--2--', 'G|--2--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'A# maj': ['e|--1--', 'B|--3--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'Bb maj': ['e|--1--', 'B|--3--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'B maj': ['e|--2--', 'B|--4--', 'G|--4--', 'D|--4--', 'A|--2--', 'E|--x--'],
    
    # Minor chords
    'C min': ['e|--3--', 'B|--4--', 'G|--5--', 'D|--5--', 'A|--3--', 'E|--x--'],
    'C# min': ['e|--4--', 'B|--5--', 'G|--6--', 'D|--6--', 'A|--4--', 'E|--x--'],
    'Db min': ['e|--4--', 'B|--5--', 'G|--6--', 'D|--6--', 'A|--4--', 'E|--x--'],
    'D min': ['e|--1--', 'B|--3--', 'G|--2--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'D# min': ['e|--2--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb min': ['e|--2--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'E min': ['e|--0--', 'B|--0--', 'G|--0--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'F min': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--3--', 'A|--3--', 'E|--1--'],
    'F# min': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'Gb min': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'G min': ['e|--3--', 'B|--3--', 'G|--3--', 'D|--0--', 'A|--1--', 'E|--3--'],
    'G# min': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--6--', 'A|--6--', 'E|--4--'],
    'Ab min': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--6--', 'A|--6--', 'E|--4--'],
    'A min': ['e|--0--', 'B|--1--', 'G|--2--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'A# min': ['e|--1--', 'B|--2--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'Bb min': ['e|--1--', 'B|--2--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'B min': ['e|--2--', 'B|--3--', 'G|--4--', 'D|--4--', 'A|--2--', 'E|--x--'],
    
    # Diminished chords
    'C dim': ['e|--2--', 'B|--3--', 'G|--2--', 'D|--3--', 'A|--x--', 'E|--x--'],
    'C# dim': ['e|--3--', 'B|--4--', 'G|--3--', 'D|--4--', 'A|--x--', 'E|--x--'],
    'Db dim': ['e|--3--', 'B|--4--', 'G|--3--', 'D|--4--', 'A|--x--', 'E|--x--'],
    'D dim': ['e|--4--', 'B|--2--', 'G|--1--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'D# dim': ['e|--2--', 'B|--3--', 'G|--2--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb dim': ['e|--2--', 'B|--3--', 'G|--2--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'E dim': ['e|--3--', 'B|--1--', 'G|--0--', 'D|--2--', 'A|--x--', 'E|--x--'],
    'F dim': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--x--'],
    'F# dim': ['e|--2--', 'B|--0--', 'G|--2--', 'D|--4--', 'A|--x--', 'E|--x--'],
    'Gb dim': ['e|--2--', 'B|--0--', 'G|--2--', 'D|--4--', 'A|--x--', 'E|--x--'],
    'G dim': ['e|--3--', 'B|--1--', 'G|--3--', 'D|--2--', 'A|--x--', 'E|--x--'],
    'G# dim': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--x--'],
    'Ab dim': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--x--'],
    'A dim': ['e|--2--', 'B|--0--', 'G|--2--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'A# dim': ['e|--3--', 'B|--1--', 'G|--3--', 'D|--2--', 'A|--x--', 'E|--x--'],
    'Bb dim': ['e|--3--', 'B|--1--', 'G|--3--', 'D|--2--', 'A|--x--', 'E|--x--'],
    'B dim': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--x--'],
    
    # Seventh chords
    'C7': ['e|--0--', 'B|--1--', 'G|--3--', 'D|--2--', 'A|--3--', 'E|--x--'],
    'C maj7': ['e|--0--', 'B|--0--', 'G|--0--', 'D|--2--', 'A|--3--', 'E|--x--'],
    'C m7': ['e|--3--', 'B|--4--', 'G|--3--', 'D|--5--', 'A|--3--', 'E|--x--'],
    'D7': ['e|--2--', 'B|--1--', 'G|--2--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'D maj7': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'D m7': ['e|--1--', 'B|--1--', 'G|--2--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'E7': ['e|--0--', 'B|--3--', 'G|--1--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'E maj7': ['e|--0--', 'B|--0--', 'G|--1--', 'D|--1--', 'A|--2--', 'E|--0--'],
    'E m7': ['e|--0--', 'B|--3--', 'G|--0--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'F7': ['e|--1--', 'B|--1--', 'G|--2--', 'D|--1--', 'A|--3--', 'E|--1--'],
    'F maj7': ['e|--1--', 'B|--1--', 'G|--2--', 'D|--2--', 'A|--3--', 'E|--1--'],
    'F m7': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--1--', 'A|--3--', 'E|--1--'],
    'G7': ['e|--1--', 'B|--0--', 'G|--0--', 'D|--0--', 'A|--2--', 'E|--3--'],
    'G maj7': ['e|--2--', 'B|--0--', 'G|--0--', 'D|--0--', 'A|--2--', 'E|--3--'],
    'G m7': ['e|--3--', 'B|--3--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--3--'],
    'A7': ['e|--0--', 'B|--2--', 'G|--0--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'A maj7': ['e|--0--', 'B|--2--', 'G|--1--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'A m7': ['e|--0--', 'B|--1--', 'G|--0--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'B7': ['e|--2--', 'B|--0--', 'G|--2--', 'D|--1--', 'A|--2--', 'E|--x--'],
    'B maj7': ['e|--2--', 'B|--4--', 'G|--3--', 'D|--4--', 'A|--2--', 'E|--x--'],
    'B m7': ['e|--2--', 'B|--3--', 'G|--2--', 'D|--4--', 'A|--2--', 'E|--x--'],
    
    # Ninth chords
    'C9': ['e|--3--', 'B|--3--', 'G|--3--', 'D|--2--', 'A|--3--', 'E|--x--'],
    'D9': ['e|--0--', 'B|--3--', 'G|--2--', 'D|--4--', 'A|--5--', 'E|--x--'],
    'E9': ['e|--2--', 'B|--0--', 'G|--1--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'F9': ['e|--1--', 'B|--1--', 'G|--2--', 'D|--1--', 'A|--1--', 'E|--1--'],
    'G9': ['e|--3--', 'B|--3--', 'G|--0--', 'D|--2--', 'A|--x--', 'E|--3--'],
    'A9': ['e|--0--', 'B|--0--', 'G|--0--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'B9': ['e|--2--', 'B|--1--', 'G|--2--', 'D|--1--', 'A|--2--', 'E|--x--'],
    
    # Augmented chords
    'C aug': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--2--', 'A|--3--', 'E|--x--'],
    'D aug': ['e|--3--', 'B|--3--', 'G|--3--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'E aug': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'F aug': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--3--', 'A|--3--', 'E|--1--'],
    'G aug': ['e|--0--', 'B|--1--', 'G|--0--', 'D|--1--', 'A|--2--', 'E|--3--'],
    'A aug': ['e|--1--', 'B|--2--', 'G|--2--', 'D|--3--', 'A|--0--', 'E|--x--'],
    'B aug': ['e|--3--', 'B|--4--', 'G|--4--', 'D|--5--', 'A|--2--', 'E|--x--'],
    
    # Suspended chords
    'C sus2': ['e|--3--', 'B|--1--', 'G|--0--', 'D|--0--', 'A|--3--', 'E|--x--'],
    'C sus4': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--3--', 'A|--3--', 'E|--x--'],
    'C# sus2': ['e|--4--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--4--', 'E|--x--'],
    'C# sus4': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--4--', 'A|--4--', 'E|--x--'],
    'Db sus2': ['e|--4--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--4--', 'E|--x--'],
    'Db sus4': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--4--', 'A|--4--', 'E|--x--'],
    'D sus2': ['e|--0--', 'B|--3--', 'G|--2--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'D sus4': ['e|--3--', 'B|--3--', 'G|--2--', 'D|--0--', 'A|--x--', 'E|--x--'],
    'D# sus2': ['e|--1--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'D# sus4': ['e|--4--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb sus2': ['e|--1--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb sus4': ['e|--4--', 'B|--4--', 'G|--3--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'E sus2': ['e|--0--', 'B|--0--', 'G|--4--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'E sus4': ['e|--0--', 'B|--0--', 'G|--2--', 'D|--2--', 'A|--2--', 'E|--0--'],
    'F sus2': ['e|--1--', 'B|--1--', 'G|--3--', 'D|--3--', 'A|--3--', 'E|--1--'],
    'F sus4': ['e|--1--', 'B|--1--', 'G|--3--', 'D|--3--', 'A|--3--', 'E|--1--'],
    'F# sus2': ['e|--2--', 'B|--2--', 'G|--4--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'F# sus4': ['e|--2--', 'B|--2--', 'G|--4--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'Gb sus2': ['e|--2--', 'B|--2--', 'G|--4--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'Gb sus4': ['e|--2--', 'B|--2--', 'G|--4--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'G sus2': ['e|--0--', 'B|--0--', 'G|--0--', 'D|--0--', 'A|--2--', 'E|--3--'],
    'G sus4': ['e|--1--', 'B|--1--', 'G|--0--', 'D|--0--', 'A|--2--', 'E|--3--'],
    'G# sus2': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--4--'],
    'G# sus4': ['e|--2--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--4--'],
    'Ab sus2': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--4--'],
    'Ab sus4': ['e|--2--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--4--'],
    'A sus2': ['e|--0--', 'B|--0--', 'G|--2--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'A sus4': ['e|--0--', 'B|--3--', 'G|--2--', 'D|--2--', 'A|--0--', 'E|--x--'],
    'A# sus2': ['e|--1--', 'B|--1--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'A# sus4': ['e|--1--', 'B|--4--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'Bb sus2': ['e|--1--', 'B|--1--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'Bb sus4': ['e|--1--', 'B|--4--', 'G|--3--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'B sus2': ['e|--2--', 'B|--2--', 'G|--4--', 'D|--4--', 'A|--2--', 'E|--x--'],
    'B sus4': ['e|--2--', 'B|--5--', 'G|--4--', 'D|--4--', 'A|--2--', 'E|--x--'],
    
    # Additional extended chords for comprehensive coverage
    'C# 7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--4--', 'A|--4--', 'E|--x--'],
    'C# maj7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--5--', 'A|--4--', 'E|--x--'],
    'C# m7': ['e|--4--', 'B|--5--', 'G|--4--', 'D|--6--', 'A|--4--', 'E|--x--'],
    'Db 7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--4--', 'A|--4--', 'E|--x--'],
    'Db maj7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--5--', 'A|--4--', 'E|--x--'],
    'Db m7': ['e|--4--', 'B|--5--', 'G|--4--', 'D|--6--', 'A|--4--', 'E|--x--'],
    'D# 7': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'D# maj7': ['e|--1--', 'B|--3--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'D# m7': ['e|--2--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb 7': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb maj7': ['e|--1--', 'B|--3--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb m7': ['e|--2--', 'B|--2--', 'G|--1--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'F# 7': ['e|--2--', 'B|--2--', 'G|--3--', 'D|--2--', 'A|--4--', 'E|--2--'],
    'F# maj7': ['e|--2--', 'B|--2--', 'G|--3--', 'D|--3--', 'A|--4--', 'E|--2--'],
    'F# m7': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--2--', 'A|--4--', 'E|--2--'],
    'Gb 7': ['e|--2--', 'B|--2--', 'G|--3--', 'D|--2--', 'A|--4--', 'E|--2--'],
    'Gb maj7': ['e|--2--', 'B|--2--', 'G|--3--', 'D|--3--', 'A|--4--', 'E|--2--'],
    'Gb m7': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--2--', 'A|--4--', 'E|--2--'],
    'G# 7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--4--', 'A|--6--', 'E|--4--'],
    'G# maj7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--5--', 'A|--6--', 'E|--4--'],
    'G# m7': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--4--', 'A|--6--', 'E|--4--'],
    'Ab 7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--4--', 'A|--6--', 'E|--4--'],
    'Ab maj7': ['e|--4--', 'B|--4--', 'G|--5--', 'D|--5--', 'A|--6--', 'E|--4--'],
    'Ab m7': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--4--', 'A|--6--', 'E|--4--'],
    'A# 7': ['e|--1--', 'B|--1--', 'G|--2--', 'D|--1--', 'A|--1--', 'E|--x--'],
    'A# maj7': ['e|--1--', 'B|--3--', 'G|--2--', 'D|--2--', 'A|--1--', 'E|--x--'],
    'A# m7': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'Bb 7': ['e|--1--', 'B|--1--', 'G|--2--', 'D|--1--', 'A|--1--', 'E|--x--'],
    'Bb maj7': ['e|--1--', 'B|--3--', 'G|--2--', 'D|--2--', 'A|--1--', 'E|--x--'],
    'Bb m7': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--3--', 'A|--1--', 'E|--x--'],
    
    # Additional ninth chords
    'C# 9': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--4--', 'A|--4--', 'E|--x--'],
    'Db 9': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--4--', 'A|--4--', 'E|--x--'],
    'D# 9': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--x--'],
    'Eb 9': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--x--'],
    'F# 9': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--2--', 'A|--2--', 'E|--2--'],
    'Gb 9': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--2--', 'A|--2--', 'E|--2--'],
    'G# 9': ['e|--4--', 'B|--4--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--4--'],
    'Ab 9': ['e|--4--', 'B|--4--', 'G|--1--', 'D|--3--', 'A|--x--', 'E|--4--'],
    'A# 9': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--3--', 'A|--1--', 'E|--x--'],
    'Bb 9': ['e|--1--', 'B|--1--', 'G|--1--', 'D|--3--', 'A|--1--', 'E|--x--'],
    
    # Additional augmented chords
    'C# aug': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--3--', 'A|--4--', 'E|--x--'],
    'Db aug': ['e|--2--', 'B|--2--', 'G|--2--', 'D|--3--', 'A|--4--', 'E|--x--'],
    'D# aug': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'Eb aug': ['e|--4--', 'B|--4--', 'G|--4--', 'D|--1--', 'A|--x--', 'E|--x--'],
    'F# aug': ['e|--3--', 'B|--3--', 'G|--3--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'Gb aug': ['e|--3--', 'B|--3--', 'G|--3--', 'D|--4--', 'A|--4--', 'E|--2--'],
    'G# aug': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--2--', 'A|--x--', 'E|--4--'],
    'Ab aug': ['e|--1--', 'B|--2--', 'G|--1--', 'D|--2--', 'A|--x--', 'E|--4--'],
    'A# aug': ['e|--2--', 'B|--3--', 'G|--3--', 'D|--4--', 'A|--1--', 'E|--x--'],
    'Bb aug': ['e|--2--', 'B|--3--', 'G|--3--', 'D|--4--', 'A|--1--', 'E|--x--']
}

def get_scale(key, scale_type='major'):
    """Generate scale for given key and scale type"""
    if scale_type not in SCALE_INTERVALS:
        scale_type = 'major'
    
    idx = NOTE_NAMES.index(key)
    intervals = SCALE_INTERVALS[scale_type]
    return [NOTE_NAMES[(idx + i) % 12] for i in intervals]

def generate_basic_tablature(chord_name):
    """Generate a basic tablature for missing chords"""
    if not chord_name or ' ' not in chord_name:
        return ['e|--x--', 'B|--x--', 'G|--x--', 'D|--x--', 'A|--x--', 'E|--x--']
    
    parts = chord_name.split(' ', 1)
    root_note = parts[0]
    chord_type = parts[1] if len(parts) > 1 else 'maj'
    
    # Get root note index
    try:
        root_idx = NOTE_NAMES.index(root_note)
    except ValueError:
        return ['e|--x--', 'B|--x--', 'G|--x--', 'D|--x--', 'A|--x--', 'E|--x--']
    
    # Try to find a similar chord pattern first
    for existing_chord, tablature in TABLATURES.items():
        if existing_chord.endswith(f' {chord_type}'):
            existing_root = existing_chord.split(' ')[0]
            try:
                existing_idx = NOTE_NAMES.index(existing_root)
                # Transpose the tablature
                semitone_diff = (root_idx - existing_idx) % 12
                transposed_tab = []
                for string in tablature:
                    if '--x--' in string:
                        transposed_tab.append(string)
                    else:
                        # Extract fret number and transpose
                        fret_match = string.split('--')[1].split('--')[0]
                        try:
                            fret = int(fret_match)
                            new_fret = (fret + semitone_diff) % 12
                            if new_fret > 12:
                                new_fret = new_fret % 12
                            string_name = string.split('|')[0]
                            transposed_tab.append(f'{string_name}|--{new_fret}--')
                        except ValueError:
                            transposed_tab.append(string)
                return transposed_tab
            except (ValueError, IndexError):
                continue
    
    # Fallback: create a basic major chord pattern transposed to the root
    basic_pattern = ['e|--0--', 'B|--1--', 'G|--0--', 'D|--2--', 'A|--3--', 'E|--x--']  # C major pattern
    c_idx = NOTE_NAMES.index('C')
    semitone_diff = (root_idx - c_idx) % 12
    
    transposed_tab = []
    for string in basic_pattern:
        if '--x--' in string:
            transposed_tab.append(string)
        else:
            fret_match = string.split('--')[1].split('--')[0]
            try:
                fret = int(fret_match)
                new_fret = fret + semitone_diff
                if new_fret > 12:
                    new_fret = new_fret % 12
                string_name = string.split('|')[0]
                transposed_tab.append(f'{string_name}|--{new_fret}--')
            except ValueError:
                transposed_tab.append(string)
    
    return transposed_tab

def grado_to_accordo(key, grado, scale_type='major'):
    """Convert Roman numeral degree to chord name with comprehensive chord type support"""
    # Get the appropriate degree mapping for the scale
    if scale_type not in DEGREE_MAPPINGS:
        scale_type = 'major'
    
    degree_map = DEGREE_MAPPINGS[scale_type]['degrees']
    type_map = DEGREE_MAPPINGS[scale_type]['types']
    
    # Direct lookup first (for extended chords like I7, V9, etc.)
    if grado in degree_map and grado in type_map:
        scale = get_scale(key, scale_type)
        index = degree_map[grado]
        nota = scale[index]
        chord_type = type_map[grado]
        return f"{nota} {chord_type}"
    
    # Parse complex chord notation
    original_grado = grado
    base = grado
    
    # Remove extensions to find base degree
    extensions = ['maj7', 'm7', '°7', '+7', 'sus4', 'sus2', '9', '7', '°', '+']
    found_extension = ""
    
    for ext in extensions:
        if ext in grado:
            found_extension = ext
            base = grado.replace(ext, "")
            break
    
    # Get chord type from mapping or use the found extension
    if original_grado in type_map:
        chord_type = type_map[original_grado]
    elif found_extension:
        chord_type = found_extension
    else:
        chord_type = type_map.get(base, "maj")
    
    # Handle special flat/sharp degrees
    if base.startswith("b") or base.startswith("#"):
        scale = get_scale(key, scale_type)
        
        # Handle flat degrees
        if base == "bVII" or base == "bvii":
            root_idx = NOTE_NAMES.index(scale[6])
            flat_degree = NOTE_NAMES[(root_idx - 1) % 12]
            return f"{flat_degree} {chord_type}"
        elif base == "bVI":
            root_idx = NOTE_NAMES.index(scale[5])
            flat_degree = NOTE_NAMES[(root_idx - 1) % 12]
            return f"{flat_degree} {chord_type}"
        elif base == "bIII" or base == "biii":
            root_idx = NOTE_NAMES.index(scale[2])
            flat_degree = NOTE_NAMES[(root_idx - 1) % 12]
            return f"{flat_degree} {chord_type}"
        elif base == "bII":
            root_idx = NOTE_NAMES.index(scale[1])
            flat_degree = NOTE_NAMES[(root_idx - 1) % 12]
            return f"{flat_degree} {chord_type}"
        elif base == "bV":
            root_idx = NOTE_NAMES.index(scale[4])
            flat_degree = NOTE_NAMES[(root_idx - 1) % 12]
            return f"{flat_degree} {chord_type}"
        # Handle sharp degrees
        elif base == "#iv" or base == "#IV":
            root_idx = NOTE_NAMES.index(scale[3])
            sharp_degree = NOTE_NAMES[(root_idx + 1) % 12]
            return f"{sharp_degree} {chord_type}"
    
    # Standard degree lookup
    if base in degree_map:
        scale = get_scale(key, scale_type)
        index = degree_map[base]
        nota = scale[index]
        return f"{nota} {chord_type}"
    
    # Handle Roman numeral cases
    roman_map = {
        'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'VI': 5, 'VII': 6,
        'i': 0, 'ii': 1, 'iii': 2, 'iv': 3, 'v': 4, 'vi': 5, 'vii': 6
    }
    
    if base in roman_map:
        scale = get_scale(key, scale_type)
        index = roman_map[base]
        nota = scale[index]
        return f"{nota} {chord_type}"
    
    # Fallback
    return f"{key} {chord_type}"

# Initialize database tables  
def init_db():
    if database_url:
        import models
        db.create_all()

# Initialize database in app context
if database_url:
    with app.app_context():
        init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_progression():
    """Generate chord progression based on user selections"""
    data = request.get_json()
    key = data.get('key', 'C')
    scale_type = data.get('scale', 'major')
    style = data.get('style', 'pop').lower()
    rhythm = data.get('rhythm', 'moderato').lower()
    
    # Determine number of chords based on rhythm
    rhythm_map = {"lento": 3, "moderato": 6, "veloce": 9}
    n_chords = rhythm_map.get(rhythm, 6)
    
    # Get chord progression for style and scale
    style_progressions = PROGRESSIONI.get(style, {"major": ["I", "IV", "V"]})
    if isinstance(style_progressions, dict):
        gradi = style_progressions.get(scale_type, ["I", "IV", "V"])
    else:
        gradi = style_progressions
    scelti = random.choices(gradi, k=n_chords)
    
    # Generate scale notes
    scale_notes = get_scale(key, scale_type)
    scale_display_name = SCALE_NAMES.get(scale_type, scale_type.title())
    
    # Generate result
    result = {
        'title': f"{style.title()} – {key} {scale_display_name}",
        'scale_notes': scale_notes,
        'scale_name': f"{key} {scale_display_name}",
        'chords': []
    }
    
    for grado in scelti:
        chord_name = grado_to_accordo(key, grado, scale_type)
        tablature = TABLATURES.get(chord_name, [])
        
        # If tablature is missing, try to generate a basic one
        if not tablature:
            tablature = generate_basic_tablature(chord_name)
        
        result['chords'].append({
            'name': chord_name,
            'degree': grado,
            'tablature': tablature
        })
    
    # Update statistics if database is available
    if database_url:
        try:
            from models import UserStatistics
            stats = UserStatistics.query.first()
            if not stats:
                stats = UserStatistics()
                db.session.add(stats)
            
            stats.total_progressions_generated = (stats.total_progressions_generated or 0) + 1
            stats.most_used_key = key
            stats.most_used_scale = scale_type
            stats.most_used_style = style
            stats.updated_at = datetime.utcnow()
            
            db.session.commit()
        except Exception as e:
            print(f"Database error: {e}")
            db.session.rollback()
    
    return jsonify(result)

@app.route('/save-progression', methods=['POST'])
def save_progression():
    """Save a chord progression to the database"""
    if not database_url:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        from models import SavedProgression
        
        data = request.get_json()
        name = data.get('name', f"Progressione {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        key_signature = data.get('key', 'C')
        scale_type = data.get('scale', 'major')
        style = data.get('style', 'pop')
        rhythm = data.get('rhythm', 'moderato')
        chords_data = data.get('chords', [])
        scale_notes = data.get('scale_notes', [])
        
        # Check if a similar progression already exists
        existing = SavedProgression.query.filter_by(
            key_signature=key_signature,
            scale_type=scale_type,
            style=style,
            rhythm=rhythm
        ).first()
        
        if existing:
            # Update existing progression
            existing.times_generated += 1
            existing.name = name
            existing.set_chords_data(chords_data)
            existing.set_scale_notes(scale_notes)
            db.session.commit()
            return jsonify({'message': 'Progressione aggiornata', 'id': existing.id})
        else:
            # Create new progression
            progression = SavedProgression()
            progression.name = name
            progression.key_signature = key_signature
            progression.scale_type = scale_type
            progression.style = style
            progression.rhythm = rhythm
            progression.set_chords_data(chords_data)
            progression.set_scale_notes(scale_notes)
            
            db.session.add(progression)
            db.session.commit()
            
            return jsonify({'message': 'Progressione salvata', 'id': progression.id})
            
    except Exception as e:
        print(f"Error saving progression: {e}")
        db.session.rollback()
        return jsonify({'error': 'Errore nel salvataggio'}), 500

@app.route('/saved-progressions', methods=['GET'])
def get_saved_progressions():
    """Get all saved progressions"""
    if not database_url:
        return jsonify({'progressions': []})
    
    try:
        from models import SavedProgression
        
        progressions = SavedProgression.query.order_by(SavedProgression.created_at.desc()).all()
        return jsonify({
            'progressions': [p.to_dict() for p in progressions]
        })
        
    except Exception as e:
        print(f"Error retrieving progressions: {e}")
        return jsonify({'progressions': []})

@app.route('/progression/<int:progression_id>', methods=['GET'])
def get_progression(progression_id):
    """Get a specific saved progression"""
    if not database_url:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        from models import SavedProgression
        
        progression = SavedProgression.query.get_or_404(progression_id)
        return jsonify(progression.to_dict())
        
    except Exception as e:
        print(f"Error retrieving progression: {e}")
        return jsonify({'error': 'Progressione non trovata'}), 404

@app.route('/progression/<int:progression_id>/favorite', methods=['POST'])
def toggle_favorite(progression_id):
    """Toggle favorite status of a progression"""
    if not database_url:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        from models import SavedProgression
        
        progression = SavedProgression.query.get_or_404(progression_id)
        progression.is_favorite = not progression.is_favorite
        db.session.commit()
        
        return jsonify({
            'message': 'Preferenza aggiornata',
            'is_favorite': progression.is_favorite
        })
        
    except Exception as e:
        print(f"Error toggling favorite: {e}")
        db.session.rollback()
        return jsonify({'error': 'Errore nell\'aggiornamento'}), 500

@app.route('/progression/<int:progression_id>', methods=['DELETE'])
def delete_progression(progression_id):
    """Delete a saved progression"""
    if not database_url:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        from models import SavedProgression
        
        progression = SavedProgression.query.get_or_404(progression_id)
        db.session.delete(progression)
        db.session.commit()
        
        return jsonify({'message': 'Progressione eliminata'})
        
    except Exception as e:
        print(f"Error deleting progression: {e}")
        db.session.rollback()
        return jsonify({'error': 'Errore nell\'eliminazione'}), 500

@app.route('/statistics', methods=['GET'])
def get_statistics():
    """Get user statistics"""
    if not database_url:
        return jsonify({
            'total_progressions_generated': 0,
            'most_used_key': 'C',
            'most_used_scale': 'major',
            'most_used_style': 'pop'
        })
    
    try:
        from models import UserStatistics, SavedProgression
        
        stats = UserStatistics.query.first()
        saved_count = SavedProgression.query.count()
        favorites_count = SavedProgression.query.filter_by(is_favorite=True).count()
        
        if stats:
            result = stats.to_dict()
            result['saved_progressions'] = saved_count
            result['favorite_progressions'] = favorites_count
            return jsonify(result)
        else:
            return jsonify({
                'total_progressions_generated': 0,
                'most_used_key': 'C',
                'most_used_scale': 'major',
                'most_used_style': 'pop',
                'saved_progressions': saved_count,
                'favorite_progressions': favorites_count
            })
            
    except Exception as e:
        print(f"Error retrieving statistics: {e}")
        return jsonify({
            'total_progressions_generated': 0,
            'most_used_key': 'C',
            'most_used_scale': 'major',
            'most_used_style': 'pop',
            'saved_progressions': 0,
            'favorite_progressions': 0
        })

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    """Generate and download PDF of chord progression"""
    data = request.get_json()
    key = data.get('key', 'C')
    scale_type = data.get('scale', 'major')
    style = data.get('style', 'pop').lower()
    rhythm = data.get('rhythm', 'moderato').lower()
    chords_data = data.get('chords', [])
    scale_notes = data.get('scale_notes', [])
    scale_name = data.get('scale_name', f'{key} Maggiore')
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        textColor=blue,
        alignment=1  # Center alignment
    )
    chord_style = ParagraphStyle(
        'ChordStyle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=10,
        textColor=black
    )
    tab_style = ParagraphStyle(
        'TabStyle',
        parent=styles['Code'],
        fontSize=10,
        fontName='Courier',
        leftIndent=20,
        spaceAfter=20,
        textColor=gray
    )
    
    # Build document content
    content = []
    
    # Title
    title_text = f"{style.title()} - {scale_name}"
    content.append(Paragraph(title_text, title_style))
    content.append(Spacer(1, 20))
    
    # Scale notes display
    if scale_notes:
        scale_text = f"Note della scala: {' - '.join(scale_notes)}"
        scale_style = ParagraphStyle(
            'ScaleStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=blue,
            alignment=1,
            spaceAfter=20
        )
        content.append(Paragraph(scale_text, scale_style))
    
    # Generation info
    rhythm_names = {"lento": "Lento", "moderato": "Moderato", "veloce": "Veloce"}
    info_text = f"Ritmo: {rhythm_names.get(rhythm, rhythm.title())} ({len(chords_data)} accordi)<br/>Generato il: {datetime.now().strftime('%d/%m/%Y alle %H:%M')}"
    content.append(Paragraph(info_text, styles['Normal']))
    content.append(Spacer(1, 30))
    
    # Chords and tablatures
    for i, chord in enumerate(chords_data, 1):
        # Chord name and degree
        chord_text = f"{i}. {chord['name']} ({chord['degree']})"
        content.append(Paragraph(chord_text, chord_style))
        
        # Tablature
        if chord.get('tablature'):
            tab_text = "Tablatura:<br/>" + "<br/>".join(chord['tablature'])
            content.append(Paragraph(tab_text, tab_style))
        else:
            content.append(Paragraph("Tablatura non disponibile", tab_style))
        
        content.append(Spacer(1, 15))
    
    # Footer
    content.append(Spacer(1, 30))
    footer_text = "Generato da Generatore di Accordi con Tablature"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=gray,
        alignment=1  # Center alignment
    )
    content.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"progressione_{style}_{key}_{timestamp}.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

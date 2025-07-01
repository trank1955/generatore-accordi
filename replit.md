# Guitar Chord Generator - System Architecture

## Overview

This is a Flask-based web application that generates guitar chord progressions with tablatures. The application allows users to select musical keys, styles (pop, rock, jazz), and rhythms to generate custom chord progressions with corresponding guitar tablatures for practice and composition.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **UI Framework**: Bootstrap 5 with dark theme
- **JavaScript**: Vanilla JavaScript for dynamic interactions
- **Styling**: Custom CSS with gradient backgrounds and glassmorphism effects
- **Icons**: Font Awesome for visual elements

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Structure**: Single-file application with modular functions
- **Session Management**: Flask sessions with configurable secret key
- **API Design**: RESTful endpoints returning JSON responses

### Music Theory Engine
- **Note System**: 12-tone chromatic scale representation
- **Scale Generation**: Major scale interval calculations
- **Chord Mapping**: Roman numeral analysis to chord names
- **Tablature Database**: Static chord fingering patterns for guitar

## Key Components

### Core Musical Components
1. **Note Names Array**: Chromatic scale representation (`NOTE_NAMES`)
2. **Scale Intervals**: Major scale formula (`MAJOR_SCALE_INTERVALS`)
3. **Chord Degrees**: Roman numeral to chord type mapping
4. **Progression Library**: Style-based chord progression templates
5. **Tablature Dictionary**: Guitar fingering patterns for common chords

### Web Components
1. **Main Application** (`app.py`): Core Flask application with music theory logic
2. **Entry Point** (`main.py`): Application runner with development configuration
3. **Frontend Interface** (`templates/index.html`): User interface with form controls
4. **Dynamic Behavior** (`static/script.js`): AJAX requests and DOM manipulation
5. **Visual Styling** (`static/style.css`): Custom UI theming

### Incomplete Implementation
- The `grado_to_accordo` function is incomplete (cuts off mid-implementation)
- Missing route handlers for the `/generate` endpoint
- Incomplete JavaScript functionality references

## Data Flow

1. **User Input**: Select musical key, style, and rhythm via dropdown menus
2. **Client Request**: JavaScript sends POST request to `/generate` endpoint
3. **Server Processing**: 
   - Parse user parameters
   - Generate scale based on selected key
   - Select progression pattern based on style
   - Convert Roman numerals to chord names
   - Retrieve corresponding tablatures
4. **Response Generation**: Return JSON with chord names and tablature data
5. **Client Rendering**: Display results with chord names and visual tablatures

## External Dependencies

### Python Packages
- **Flask**: Web framework for routing and templating
- **os**: Environment variable management for configuration

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome 6**: Icon library for UI elements
- **Custom CSS**: Application-specific styling

### Browser APIs
- **Fetch API**: For asynchronous HTTP requests
- **DOM API**: For dynamic content manipulation

## Deployment Strategy

### Development Configuration
- **Host**: `0.0.0.0` (accepts connections from any interface)
- **Port**: `5000` (standard Flask development port)
- **Debug Mode**: Enabled for development with hot reloading
- **Secret Key**: Environment variable with fallback default

### Environment Variables
- `SESSION_SECRET`: Configurable session security key

### Static Asset Serving
- Flask serves static files (CSS, JavaScript) from `/static` directory
- Template files served from `/templates` directory

## Changelog

- June 29, 2025. Initial setup
- June 29, 2025. Added PDF download functionality with ReportLab integration
- June 29, 2025. Added comprehensive scale support (9 scales total)
- June 29, 2025. Added PostgreSQL database integration

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

✓ Converted KivyMD Python script to Flask web application
✓ Implemented complete chord progression generation logic
✓ Added 9 different scales (Major, Minor, Dorian, Phrygian, Lydian, Mixolydian, Locrian, Harmonic Minor, Melodic Minor)
✓ Display of 7 scale notes at the top of progressions
✓ Style-specific chord progressions for each scale type
✓ PDF download functionality with scale notes included
✓ PostgreSQL database integration with Flask-SQLAlchemy
✓ Save/load chord progressions functionality
✓ Favorite progressions and user statistics tracking
✓ Database API endpoints for CRUD operations

### Database Features

- Save chord progressions with custom names
- View saved progressions in modal interface
- Mark progressions as favorites
- Delete unwanted progressions
- Load saved progressions to recreate them
- User statistics tracking (total generated, most used keys/scales/styles)
- Automatic duplicate detection and updating

### Database Models

- SavedProgression: Stores chord progressions with metadata
- UserStatistics: Tracks usage patterns and preferences

### Latest Enhancement - Extended Chord Types

✓ Comprehensive tablature database (120+ chord fingerings)
✓ Extended chord support: 7th, 9th, diminished, augmented, suspended chords
✓ Enhanced progression generation with sophisticated harmony
✓ All chord types integrated into style-specific progressions

### Tablature Database Coverage

- **Major chords**: All 12 keys with standard fingerings
- **Minor chords**: All 12 keys with standard fingerings  
- **Diminished chords**: All 12 keys with proper voicings
- **Seventh chords**: Major 7th, minor 7th, dominant 7th for common keys
- **Ninth chords**: Extended harmony for jazz and contemporary styles
- **Augmented chords**: All 12 keys with augmented triads
- **Suspended chords**: sus2 and sus4 variations for all keys

### Advanced Progressions

- **Pop**: Basic triads plus 7th chords, suspended chords, and 9th chords
- **Rock**: Power chord feel with 7th chords and diminished passing chords
- **Jazz**: Heavy use of extended harmony (7th, 9th, sus chords) and altered chords

### Notes for Development

1. **Audio Integration**: Could add chord audio playback using Web Audio API
2. **MIDI Export**: Export progressions as MIDI files for DAW integration
3. **Chord Diagrams**: Visual chord diagrams alongside tablatures
4. **Advanced Theory**: Add chord function analysis and voice leading
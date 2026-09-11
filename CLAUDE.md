# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LekdeDai is a simplified Thai Django-based lottery prediction website. The main page displays lottery numbers for the next draw (not daily numbers) generated from four core features:

1. **News Analysis** - Analyze news from the latest lottery draw to present date
2. **Historical Lottery Analysis** - Use various formulas and AI to analyze past lottery results
3. **Dream Interpretation** - Convert dreams into lottery numbers
4. **Online Lottery Checker** - Check lottery results online (already working well)

All other features have been removed to focus on these core functionalities.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python app/manage.py migrate

# Create superuser
python app/manage.py createsuperuser

# Run development server
cd app && python manage.py runserver

# Run tests
cd app && python manage.py test
```

### Production Deployment (no Docker)

```bash
# Deploy to Linux server (fail-fast: pull -> migrate -> collectstatic -> restart)
APP_DIR=/opt/lekdedai bash deploy/deploy.sh

# Service unit template: deploy/lekdedai.service (gunicorn, no runserver)
# Required env in /opt/lekdedai/.env: SECRET_KEY, ALLOWED_HOSTS,
# DATABASE_URL (Postgres), DJANGO_SUPERUSER_PASSWORD (see .env.example)
```

### Management Commands
Core management commands for the simplified system:

```bash
# Lottery data operations
python manage.py sync_lotto_data
python manage.py clear_and_fetch_lotto

# News analysis
python manage.py scrape_rss_feeds
python manage.py scrape_category
python manage.py analyze_existing_articles

# AI prediction generation
python manage.py generate_ai_prediction

# Dream interpretation
python manage.py add_dream_data
```

## Architecture

### Core Django Apps

- **home**: Main homepage displaying next lottery draw predictions
- **dreams**: Dream interpretation system converting dreams to lottery numbers
- **lotto_stats**: Historical lottery analysis using various formulas and AI
- **news**: News analysis from latest draw to present for lottery number extraction
- **ai_engine**: AI-powered prediction system combining all data sources
- **lottery_checker**: Online lottery result checking tool (already working)

### Simplified Architecture

The system focuses on four core data sources:
- **News Analysis**: Extract lottery-relevant numbers from recent news
- **Historical Data**: Apply statistical formulas and AI to past lottery results
- **Dream Interpretation**: Convert dream symbols to traditional lottery numbers
- **Result Checking**: Verify lottery results online

### Prediction Flow

1. Collect news from latest lottery draw to present
2. Analyze historical lottery patterns using AI and formulas
3. Process dream interpretations for number suggestions
4. Combine all sources into next draw predictions
5. Display results on main homepage

## Key Configuration

- **Language**: Thai (th) with Asia/Bangkok timezone
- **Database**: PostgreSQL via DATABASE_URL environment variable
- **Static Files**: Whitenoise middleware for production
- **Media Files**: Uploaded to app/media/
- **Dependencies**: Includes ML libraries (scikit-learn, pandas, numpy), Thai NLP (pythainlp), web scraping (beautifulsoup4), and caching (redis)

## Data Flow Patterns

### Core Features

#### News Analysis
- Scrape news from latest lottery draw to present
- Extract lottery-relevant numbers from content
- Score news relevance for lottery predictions

#### Historical Analysis
- Apply statistical formulas to past lottery results
- Use AI to identify patterns in historical data
- Generate predictions based on trends

#### Dream Interpretation
- Convert dream text to lottery numbers
- Map dream symbols to traditional Thai lottery meanings
- Provide number suggestions with interpretations

#### Lottery Checker
- Check lottery results online
- Verify winning numbers (already functional)

## Development Guidelines

### Model Patterns
- Use JSONField for complex prediction data and reasoning
- Include confidence scores for all predictions
- Track data sources and processing timestamps
- Implement soft deletes where appropriate (SET_NULL foreign keys)

### URL Structure
- `/` - Main homepage with next draw predictions
- `/dreams/` - Dream interpretation feature
- `/lotto_stats/` - Historical lottery statistics
- `/news/` - News analysis for lottery numbers
- `/ai/` - AI prediction interface
- `/lottery_checker/` - Online lottery result checker

## External Dependencies

- **PostgreSQL**: Primary database (production; SQLite for local dev)
- **Redis**: Caching and session storage
- **Thai NLP libraries**: pythainlp for text processing
- **ML Stack**: scikit-learn, pandas, numpy for predictions
- **Web Scraping**: beautifulsoup4, requests for news collection

## Production Deployment

```bash
# Deploy to Linux server (fail-fast via deploy/deploy.sh)
APP_DIR=/opt/lekdedai bash deploy/deploy.sh

# Or manually: migrate -> collectstatic -> gunicorn (no runserver)
python app/manage.py migrate --noinput
python app/manage.py collectstatic --noinput
gunicorn lekdedai.wsgi:application  # from app/ dir
```

The simplified system focuses on the core lottery prediction features that Thai users need most: news analysis, historical patterns, dream interpretation, and result checking.
# Myblog

Lightweight Django blog app with tags, comments, full‑text search, RSS feeds, and sitemaps.

This is a minimal, production-ready Django application for publishing blog posts. It includes tagging, moderated comments, search (Postgres trigram optional), RSS feeds, sitemap generation, share-by-email, reusable templates, static assets, and tests — ideal as a personal blog or starter app for larger projects.

## Features
- Posts with slugs and tags
- Commenting system with moderation hooks
- Full-text search (Postgres pg_trgm optional)
- RSS feed and sitemap support
- Share-by-email and pagination
- Reusable templates and static assets
- Tests for core functionality

## Quickstart (development)
1. Clone and enter the repo:
   git clone https://github.com/Fiow00/blog_application.git && cd blog_application
2. Create and activate a virtualenv:
   python -m venv .venv
   On Windows (PowerShell): .\.venv\Scripts\Activate.ps1
   On WSL/Linux/macOS: source .venv/bin/activate
3. Install dependencies and run:
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
Open http://127.0.0.1:8000/

#!/bin/bash
# Grace Chapel Enquiries System - Setup Script

echo ""
echo "  ✝  Grace Chapel Enquiries System Setup"
echo "  ========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment
echo "→ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "→ Installing Django and dependencies..."
pip install django Pillow python-dotenv 2>&1 | tail -5

echo ""
echo "→ Running database migrations..."
python manage.py makemigrations accounts enquiries
python manage.py migrate

echo ""
echo "→ Setting up initial data..."
python manage.py setup_initial_data

echo ""
echo "  ✝  Setup Complete!"
echo "  ====================================="
echo ""
echo "  Login Credentials:"
echo "  ─────────────────────────────────────"
echo "  Head of Unit / Admin:"
echo "    Username: admin"
echo "    Password: admin123"
echo ""
echo "  Assistants:"
echo "    Username: sister_grace / Password: church123"
echo "    Username: brother_david / Password: church123"
echo ""
echo "  To start the server, run:"
echo "    source venv/bin/activate"
echo "    python manage.py runserver"
echo ""
echo "  Then open: http://127.0.0.1:8000"
echo "  Django Admin: http://127.0.0.1:8000/django-admin/"
echo ""

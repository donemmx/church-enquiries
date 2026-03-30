# ✝ Grace Chapel — Enquiries Management System

A beautiful, full-featured Django web application for managing church enquiries, member follow-ups, messages, events, prayer requests, and more.

---

## Features

### 👥 Member Management
- Register new visitors and members with full profile details
- Track membership status (New Visitor → Full Member progression)
- Search and filter by name, status, assigned staff
- Profile page with complete activity history (notes, follow-ups, prayers, attendance)

### ✅ Follow-Up System
- Assign follow-up tasks (Call, Email, SMS, Visit, WhatsApp)
- Set priority levels (High, Medium, Low) and due dates
- Overdue alerts and completion tracking
- Head of unit can delegate to any assistant

### 📅 Events
- Create and manage church events and programs
- Event types: Service, Special Program, Retreat, Outreach, Training, Social
- Track attendance and send notifications

### 📨 Messaging
- Compose Email, SMS, Prayer Messages, Announcements
- Send to all members or specific recipients
- Draft/Schedule/Send workflow
- Message history with delivery stats

### 🙏 Prayer Requests
- Log prayer requests from members
- Anonymous option available
- Status tracking: Pending → Praying → Answered
- Testimony recording for answered prayers

### 📋 Attendance Records
- Record service attendance per member
- Support multiple service types
- Historical attendance tracking

### ⛪ Ministries
- Manage ministry departments
- Track member interest in each ministry
- Assign ministry leaders

### 🛡️ Admin Panel (Head/Admin only)
- Full system overview and statistics
- Staff management — add, edit, deactivate staff
- Monthly reports and analytics
- Top performer leaderboard
- Access to Django Admin for raw data management

### 👤 Role-Based Access Control
| Role | Access |
|------|--------|
| **Administrator** | Full system access including admin panel |
| **Head of Unit** | Full access + staff management + reports |
| **Assistant** | Members, their own follow-ups, messaging, events |
| **Viewer** | Read-only access |

---

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip

### 1. Clone / Extract the project
```bash
cd church_enquiries
```

### 2. Run the Setup Script (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Manual Setup (Alternative)
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install django Pillow python-dotenv

# Run migrations
python manage.py makemigrations accounts enquiries
python manage.py migrate

# Create sample data and default users
python manage.py setup_initial_data

# Start the server
python manage.py runserver
```

### 4. Open in browser
- **Main App:** http://127.0.0.1:8000
- **Django Admin:** http://127.0.0.1:8000/django-admin/

---

## Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Head of Unit / Admin | `admin` | `admin123` |
| Assistant | `sister_grace` | `church123` |
| Assistant | `brother_david` | `church123` |

> ⚠️ **Change these passwords before going to production!**

---

## Project Structure

```
church_enquiries/
├── church_enquiries/      # Django project settings & URLs
│   ├── settings.py
│   └── urls.py
├── enquiries/             # Main app
│   ├── models.py          # Member, FollowUp, Event, Message, Prayer, Attendance
│   ├── views.py           # All view functions
│   ├── forms.py           # Django forms
│   ├── urls.py            # URL routing
│   └── admin.py           # Django admin configuration
├── accounts/              # Authentication & user profiles
│   ├── models.py          # UserProfile with roles
│   ├── views.py           # Login, profile, staff management
│   └── urls.py
├── templates/             # All HTML templates
│   ├── base.html          # Main layout with sidebar
│   ├── enquiries/         # Feature templates
│   ├── accounts/          # Auth templates
│   └── admin_panel/       # Admin-only pages
└── setup.sh               # One-click setup script
```

---

## Email Configuration (Production)

To enable real email sending, update `church_enquiries/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Grace Chapel <your-email@gmail.com>'
```

---

## Tech Stack
- **Backend:** Django 4.x (Python)
- **Database:** SQLite (development) — easily swappable to PostgreSQL
- **Styling:** Tailwind CSS (CDN)
- **Icons:** Lucide Icons
- **Typography:** Playfair Display + DM Sans (Google Fonts)

---

*Built with ❤️ for ministry excellence.*

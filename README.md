# CiviSphere

**An Integrated Citizen Services and Community Support Portal**

Your Community. Your Services. One Platform.

---

## Features

- **Emergency Services Directory** – Search hospitals, fire stations, police stations, ambulance services, blood banks and more across cities, districts and states
- **Complaint Management** – Submit, track and manage complaints with file attachments, status history and real-time notifications
- **Blood Donor Directory** – Register as a voluntary donor and search donors by blood group and location
- **Community Locations** – Explore registered community facilities with interactive Leaflet maps
- **Important Contacts** – Admin-managed directory of essential public service contacts
- **Notifications** – Automatic alerts for complaint status updates
- **Feedback System** – Star-rated feedback submission
- **Chatbot Assistant** – FAQ-driven keyword-matching assistant
- **Admin Dashboard** – Statistics, user management, complaint oversight, emergency services CRUD
- **Dark Mode** – Full light/dark theme toggle

## Tech Stack

- **Backend**: Python, Flask, Gunicorn
- **Database**: MySQL / TiDB Cloud (SSL)
- **Frontend**: Jinja2, HTML5, CSS3, JavaScript
- **Maps**: Leaflet.js + OpenStreetMap
- **Auth**: Flask-Login, Flask-WTF (CSRF), Werkzeug (password hashing)

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/csp-project.git
   cd csp-project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate    # Linux/macOS
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and secret key
   ```

5. **Set up the database**
   ```bash
   # Run schema.sql against your MySQL/TiDB instance
   mysql -h your-host -P 4000 -u your-user -p < database/schema.sql
   ```

6. **Run locally**
   ```bash
   python run_local.py
   ```

## Deployment (Render)

1. Push this repository to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **New → Web Service** and connect your repository
4. Render will auto-detect `render.yaml` and configure the service
5. Add the required environment variables (database credentials)
6. Deploy!

## Project Structure

```
├── app/
│   ├── routes/          # Blueprint route handlers
│   ├── static/          # CSS and JavaScript
│   ├── templates/       # Jinja2 HTML templates
│   ├── models.py        # User model (Flask-Login)
│   └── __init__.py      # App factory (create_app)
├── certs/               # SSL certificate for TiDB
├── database/            # SQL schema
├── config.py            # Configuration from .env
├── extensions.py        # Flask extensions and DB connection
├── index.py             # WSGI entry point (Gunicorn)
├── run_local.py         # Local development server
├── Procfile             # Gunicorn process definition
├── render.yaml          # Render deployment blueprint
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variable template
```

## License

© 2026 CiviSphere. All rights reserved.

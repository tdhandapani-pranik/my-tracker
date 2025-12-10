# Team Task Tracker - Backend# Team Task Tracker - Backend



Flask-based REST API for Team Task Tracker with Google OAuth authentication and PostgreSQL database.Flask backend API for Team Task Tracker application with PostgreSQL database.



## 🚀 Features## Features



- Google OAuth 2.0 authentication- Google OAuth authentication

- Task management (create, read, update, delete)- User profile management

- User profile management- Task CRUD operations with filtering

- Company management- Weekly reports and analytics

- Weekly reports and analytics- PostgreSQL database support

- Session-based authentication with secure cookies

## Environment Variables

## 📋 Prerequisites

Required environment variables (set in Render dashboard):

- Python 3.9+

- PostgreSQL database (we use Neon serverless PostgreSQL)```

- Google OAuth credentialsFLASK_SECRET_KEY=your-secret-key

GOOGLE_CLIENT_ID=your-google-client-id

## 🔧 Environment VariablesGOOGLE_CLIENT_SECRET=your-google-client-secret

DATABASE_URL=your-postgresql-connection-string

Create a `.env` file with the following variables (see `.env.example`):```



```env## Deployment to Render

# Database

DATABASE_URL=postgresql://user:password@host:port/databaseThis backend is configured to deploy on Render.com



# Google OAuth### Build Command:

GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com```bash

GOOGLE_CLIENT_SECRET=your-google-client-secretpip install -r requirements.txt

```

# Flask

FLASK_SECRET_KEY=your-secret-key-here### Start Command:

FLASK_ENV=production```bash

gunicorn app:app

# URLs (for OAuth redirects and CORS)```

BACKEND_URL=https://your-backend-url.onrender.com

FRONTEND_URL=https://your-frontend-url.vercel.app### Database Initialization:

```After deployment, run once:

```bash

## 📦 Installationpython init_db.py

```

1. Install dependencies:

```bash## Local Development

pip install -r requirements.txt

``````bash

# Create virtual environment

2. Initialize the database:python -m venv venv

```bashsource venv/bin/activate  # On Windows: venv\Scripts\activate

python init_db.py

```# Install dependencies

pip install -r requirements.txt

3. Run the development server:

```bash# Set up .env file with your credentials

python app.py

```# Initialize database

python init_db.py

## 🌐 API Endpoints

# Run development server

### Authenticationpython app.py

- `GET /login` - Initiate Google OAuth login```

- `GET /auth` - OAuth callback

- `GET /logout` - Logout user## API Endpoints

- `GET /logged-out` - Logged out confirmation page

- `GET /api/me` - Get current user info### Authentication

- `GET /login` - Initiate Google OAuth

### Users- `GET /auth` - OAuth callback

- `GET /api/users` - Get all users- `GET /logout` - Logout user

- `PUT /api/profile` - Update user profile

### Users

### Tasks- `GET /api/me` - Get current user

- `GET /api/tasks?type=my|assigned` - Get tasks (filtered)- `PUT /api/profile` - Update user profile

- `POST /api/tasks` - Create new task- `GET /api/users` - Get all users

- `PUT /api/tasks/:id` - Update task

- `DELETE /api/tasks/:id` - Delete task### Tasks

- `GET /api/tasks?type=my|assigned` - Get tasks with filters

### Companies- `POST /api/tasks` - Create task

- `GET /api/companies` - Get all companies- `PUT /api/tasks/:id` - Update task

- `DELETE /api/tasks/:id` - Delete task

### Reports

- `GET /api/reports/weekly` - Get weekly statistics### Other

- `GET /api/companies` - Get companies

## 🚢 Deployment to Render- `GET /api/reports/weekly` - Get weekly statistics


### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Ready for Render deployment"

# Add remote (replace with your repo)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git push -u origin main
```

### Step 2: Create Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Render will auto-detect Python using `render.yaml`
5. Click **"Create Web Service"**

### Step 3: Set Environment Variables in Render

In Render dashboard, go to **Environment** tab and add:

```
DATABASE_URL=postgresql://neondb_owner:npg_xxx@ep-xxx.us-east-1.aws.neon.tech/neondb
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
FLASK_SECRET_KEY=your-random-secret-key
FLASK_ENV=production
BACKEND_URL=https://your-app.onrender.com
FRONTEND_URL=https://your-frontend-url.vercel.app
```

### Step 4: Initialize Database (one-time)

After first deployment succeeds:
1. In Render dashboard, go to **Shell** tab
2. Run:
```bash
python init_db.py
```

### Step 5: Update Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client
4. Add to **Authorized redirect URIs**:
   - `https://your-app.onrender.com/auth`

## 📝 Database Schema

### Users Table
- `id`, `google_id`, `email`, `name`, `avatar_url`
- `designation`, `is_profile_complete`
- `created_at`, `updated_at`

### Tasks Table
- `id`, `title`, `description`, `company`
- `priority` (HIGH, MEDIUM, LOW)
- `status` (TODO, IN_PROGRESS, DONE)
- `assigned_by_user_id`, `assigned_to_user_id`
- `due_date`, `created_at`, `updated_at`

### Companies Table
- Pre-populated with: Tabhi, Pranik.ai, Client A, Internal, Other

## 🔒 Security

- Session-based authentication with secure, HTTP-only cookies
- CORS configured for specific frontend origins
- Environment-based configuration
- Cache-control headers to prevent sensitive data caching
- `.env` file excluded from version control

## 🛠️ Tech Stack

- **Framework:** Flask 3.1.0
- **Database:** PostgreSQL (via psycopg2-binary)
- **Authentication:** Authlib for OAuth 2.0
- **Server:** Gunicorn (production)
- **CORS:** Flask-CORS

## 📄 Files Structure

```
backend/
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
├── app.py               # Main Flask application
├── init_db.py           # Database initialization script
├── render.yaml          # Render deployment configuration
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## 🐛 Troubleshooting

### Render auto-detected as Node.js
- Solution: `render.yaml` explicitly declares Python runtime

### OAuth redirect errors
- Ensure `BACKEND_URL` in Render matches your actual deployed URL
- Add the exact redirect URI to Google Cloud Console

### Database connection errors
- Verify `DATABASE_URL` is correctly set in Render environment variables
- Run `python init_db.py` in Render Shell after first deployment

### Cold start delays
- Free tier Render services sleep after 15 minutes inactivity
- First request after sleep takes ~30 seconds

## 📞 Support

For issues or questions, contact the development team.

## 📄 License

Private - All rights reserved

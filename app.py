import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, session, redirect
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# CORS configuration - allow both local and production frontend
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
CORS(app, supports_credentials=True, origins=[FRONTEND_URL, 'http://localhost:3000'])

# Set the secret key for session management
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Session configuration for production
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Get base URLs from environment
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5001')

# --- OAuth Configuration ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    server_metadata={'issuer': 'https://accounts.google.com'}
)

# --- Database Connection ---
def get_db_connection():
    return psycopg2.connect(os.environ.get('DATABASE_URL'), cursor_factory=RealDictCursor)

# --- Middleware to prevent caching ---
@app.after_request
def add_no_cache_headers(response):
    """Add headers to prevent browser caching for authenticated pages"""
    if request.path.startswith('/api/') or request.path in ['/auth', '/logout']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# --- Authentication Routes ---
@app.route('/login')
def login():
    redirect_uri = f'{BACKEND_URL}/auth'
    return google.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        user_info = dict(user_info)
    else:
        user_info = google.get('userinfo').json()

    # Get user data
    google_id = user_info.get('sub') or user_info.get('id')
    email = user_info.get('email')
    name = user_info.get('name') or email
    avatar_url = user_info.get('picture')

    if not google_id or not email:
        return "Could not retrieve user information from Google.", 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if user exists
    cur.execute('SELECT * FROM users WHERE google_id = %s', (google_id,))
    user = cur.fetchone()
    
    if not user:
        # Create new user
        cur.execute(
            '''INSERT INTO users (google_id, email, name, avatar_url, is_profile_complete) 
               VALUES (%s, %s, %s, %s, FALSE) RETURNING id, name, email, avatar_url, designation, is_profile_complete''',
            (google_id, email, name, avatar_url)
        )
        user_record = cur.fetchone()
        conn.commit()
    else:
        # Update avatar if changed
        cur.execute(
            '''UPDATE users SET avatar_url = %s WHERE google_id = %s 
               RETURNING id, name, email, avatar_url, designation, is_profile_complete''',
            (avatar_url, google_id)
        )
        user_record = cur.fetchone()
        conn.commit()

    cur.close()
    conn.close()
    
    session['user'] = {
        'id': user_record['id'],
        'name': user_record['name'],
        'email': user_record['email'],
        'avatar_url': user_record['avatar_url'],
        'designation': user_record['designation'],
        'is_profile_complete': user_record['is_profile_complete']
    }
    
    return redirect(FRONTEND_URL)

@app.route('/logout')
def logout():
    session.clear()  # Clear entire session
    response = redirect(f'{FRONTEND_URL}/logged-out')
    # Prevent caching to avoid back button issues
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# --- User API Routes ---
@app.route('/api/me')
def get_current_user():
    if 'user' in session:
        response = jsonify(session['user'])
        # Prevent caching
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user']['id']
    data = request.get_json()
    
    name = data.get('name')
    designation = data.get('designation')

    if not name or not designation:
        return jsonify({'error': 'Name and designation are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        '''UPDATE users 
           SET name = %s, designation = %s, is_profile_complete = TRUE, updated_at = CURRENT_TIMESTAMP
           WHERE id = %s
           RETURNING id, name, email, avatar_url, designation, is_profile_complete''',
        (name, designation, user_id)
    )
    
    updated_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    # Update session
    session['user'] = {
        'id': updated_user['id'],
        'name': updated_user['name'],
        'email': updated_user['email'],
        'avatar_url': updated_user['avatar_url'],
        'designation': updated_user['designation'],
        'is_profile_complete': updated_user['is_profile_complete']
    }
    
    return jsonify(session['user'])

@app.route('/api/users')
def get_all_users():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, name, email, avatar_url, designation 
        FROM users 
        WHERE is_profile_complete = TRUE
        ORDER BY name
    ''')
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(users)

# --- Company API Routes ---
@app.route('/api/companies')
def get_companies():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT name FROM companies ORDER BY name')
    companies = [row['name'] for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    return jsonify(companies)

# --- Task API Routes ---
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user']['id']
    task_type = request.args.get('type', 'my')
    status = request.args.get('status')
    priority = request.args.get('priority')
    company = request.args.get('company')
    search = request.args.get('search', '')

    conn = get_db_connection()
    cur = conn.cursor()
    
    query = '''
        SELECT 
            t.id, t.title, t.description, t.company, t.priority, t.status, 
            t.due_date, t.created_at, t.updated_at,
            assigned_by.id as assigned_by_id, assigned_by.name as assigned_by_name, 
            assigned_by.avatar_url as assigned_by_avatar,
            assigned_to.id as assigned_to_id, assigned_to.name as assigned_to_name,
            assigned_to.avatar_url as assigned_to_avatar, assigned_to.designation as assigned_to_designation
        FROM tasks t
        LEFT JOIN users assigned_by ON t.assigned_by_user_id = assigned_by.id
        LEFT JOIN users assigned_to ON t.assigned_to_user_id = assigned_to.id
        WHERE 1=1
    '''
    
    params = []
    
    if task_type == 'my':
        query += ' AND t.assigned_to_user_id = %s'
        params.append(user_id)
    elif task_type == 'assigned':
        query += ' AND t.assigned_by_user_id = %s'
        params.append(user_id)
    
    if status:
        query += ' AND t.status = %s'
        params.append(status)
    
    if priority:
        query += ' AND t.priority = %s'
        params.append(priority)
    
    if company:
        query += ' AND t.company = %s'
        params.append(company)
    
    if search:
        query += ' AND t.title ILIKE %s'
        params.append(f'%{search}%')
    
    query += ' ORDER BY t.created_at DESC'
    
    cur.execute(query, params)
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user']['id']
    data = request.get_json()
    
    title = data.get('title')
    description = data.get('description', '')
    company = data.get('company')
    priority = data.get('priority', 'MEDIUM')
    assigned_to_user_id = data.get('assigned_to_user_id')
    due_date = data.get('due_date')

    if not title or not assigned_to_user_id:
        return jsonify({'error': 'Title and assignee are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        '''INSERT INTO tasks 
           (title, description, company, priority, status, assigned_by_user_id, assigned_to_user_id, due_date)
           VALUES (%s, %s, %s, %s, 'TODO', %s, %s, %s)
           RETURNING id''',
        (title, description, company, priority, user_id, assigned_to_user_id, due_date)
    )
    
    new_task_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Task created successfully', 'id': new_task_id}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user']['id']
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        'SELECT * FROM tasks WHERE id = %s AND (assigned_to_user_id = %s OR assigned_by_user_id = %s)',
        (task_id, user_id, user_id)
    )
    task = cur.fetchone()
    
    if not task:
        cur.close()
        conn.close()
        return jsonify({'error': 'Task not found or permission denied'}), 404
    
    update_fields = []
    params = []
    
    if 'status' in data:
        update_fields.append('status = %s')
        params.append(data['status'])
    
    if 'title' in data:
        update_fields.append('title = %s')
        params.append(data['title'])
    
    if 'description' in data:
        update_fields.append('description = %s')
        params.append(data['description'])
    
    if 'priority' in data:
        update_fields.append('priority = %s')
        params.append(data['priority'])
    
    if 'company' in data:
        update_fields.append('company = %s')
        params.append(data['company'])
    
    if 'due_date' in data:
        update_fields.append('due_date = %s')
        params.append(data['due_date'])
    
    if update_fields:
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %s"
        cur.execute(query, params)
        conn.commit()
    
    cur.close()
    conn.close()
    
    return jsonify({'message': 'Task updated successfully'})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user']['id']
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        'DELETE FROM tasks WHERE id = %s AND assigned_by_user_id = %s RETURNING id',
        (task_id, user_id)
    )
    
    deleted_row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if deleted_row:
        return jsonify({'message': 'Task deleted successfully'})
    else:
        return jsonify({'error': 'Task not found or permission denied'}), 404

# --- Reports API Routes ---
@app.route('/api/reports/weekly')
def get_weekly_report():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user']['id']
    
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE assigned_to_user_id = %s 
        AND created_at >= %s
    ''', (user_id, start_of_week))
    tasks_assigned_to_me = cur.fetchone()['count']
    
    cur.execute('''
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE assigned_by_user_id = %s 
        AND created_at >= %s
    ''', (user_id, start_of_week))
    tasks_i_assigned = cur.fetchone()['count']
    
    cur.execute('''
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE assigned_to_user_id = %s 
        AND status = 'DONE'
        AND updated_at >= %s
    ''', (user_id, start_of_week))
    tasks_i_completed = cur.fetchone()['count']
    
    cur.execute('''
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE created_at >= %s
    ''', (start_of_week,))
    total_tasks_created = cur.fetchone()['count']
    
    cur.execute('''
        SELECT COUNT(*) as count 
        FROM tasks 
        WHERE status = 'DONE'
        AND updated_at >= %s
    ''', (start_of_week,))
    total_tasks_completed = cur.fetchone()['count']
    
    cur.execute('''
        SELECT status, COUNT(*) as count 
        FROM tasks 
        WHERE assigned_to_user_id = %s 
        GROUP BY status
    ''', (user_id,))
    tasks_by_status = {row['status']: row['count'] for row in cur.fetchall()}
    
    cur.execute('''
        SELECT priority, COUNT(*) as count 
        FROM tasks 
        WHERE assigned_to_user_id = %s 
        GROUP BY priority
    ''', (user_id,))
    tasks_by_priority = {row['priority']: row['count'] for row in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    return jsonify({
        'tasks_assigned_to_me_this_week': tasks_assigned_to_me,
        'tasks_i_assigned_this_week': tasks_i_assigned,
        'tasks_i_completed_this_week': tasks_i_completed,
        'total_tasks_created_this_week': total_tasks_created,
        'total_tasks_completed_this_week': total_tasks_completed,
        'tasks_by_status': tasks_by_status,
        'tasks_by_priority': tasks_by_priority
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

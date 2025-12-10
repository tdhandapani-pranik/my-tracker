import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=== Initializing Team Task Tracker Database ===\n")

# --- USERS TABLE ---
print("--- Setting up 'users' table ---")
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    designation VARCHAR(255),
    is_profile_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
""")

# Add missing columns to existing users table
columns_to_add = [
    ("avatar_url", "TEXT"),
    ("designation", "VARCHAR(255)"),
    ("is_profile_complete", "BOOLEAN DEFAULT FALSE"),
    ("updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
]

for column_name, column_type in columns_to_add:
    cur.execute(f"""
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='{column_name}'
    """)
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type};")
        print(f"  ✓ Added column '{column_name}' to users table")
    else:
        print(f"  • Column '{column_name}' already exists")

print("'users' table is ready.\n")

# --- TASKS TABLE ---
print("--- Setting up 'tasks' table ---")
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    company VARCHAR(255),
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    status VARCHAR(20) DEFAULT 'TODO',
    assigned_by_user_id INTEGER,
    assigned_to_user_id INTEGER,
    due_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assigned_by FOREIGN KEY(assigned_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_assigned_to FOREIGN KEY(assigned_to_user_id) REFERENCES users(id) ON DELETE SET NULL
);
""")

# Add/update columns for existing tasks table
task_columns_to_add = [
    ("company", "VARCHAR(255)"),
    ("priority", "VARCHAR(20) DEFAULT 'MEDIUM'"),
    ("assigned_by_user_id", "INTEGER"),
    ("assigned_to_user_id", "INTEGER"),
    ("due_date", "DATE"),
    ("updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
]

for column_name, column_type in task_columns_to_add:
    cur.execute(f"""
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tasks' AND column_name='{column_name}'
    """)
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {column_type};")
        print(f"  ✓ Added column '{column_name}' to tasks table")
    else:
        print(f"  • Column '{column_name}' already exists")

# Update status column type if needed
cur.execute("""
    ALTER TABLE tasks 
    ALTER COLUMN status TYPE VARCHAR(20),
    ALTER COLUMN status SET DEFAULT 'TODO';
""")

# Drop old user_id column and constraint if exists
cur.execute("""
    SELECT 1 FROM information_schema.columns 
    WHERE table_name='tasks' AND column_name='user_id'
""")
if cur.fetchone():
    cur.execute("ALTER TABLE tasks DROP CONSTRAINT IF EXISTS fk_user;")
    cur.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS user_id;")
    print("  ✓ Removed old 'user_id' column")

# Add foreign key constraints if they don't exist
constraints_to_add = [
    ("fk_assigned_by", "assigned_by_user_id"),
    ("fk_assigned_to", "assigned_to_user_id")
]

for constraint_name, column_name in constraints_to_add:
    cur.execute(f"""
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name='tasks' AND constraint_name='{constraint_name}'
    """)
    if not cur.fetchone():
        cur.execute(f"""
            ALTER TABLE tasks 
            ADD CONSTRAINT {constraint_name}
            FOREIGN KEY({column_name}) REFERENCES users(id) ON DELETE SET NULL;
        """)
        print(f"  ✓ Added foreign key '{constraint_name}'")
    else:
        print(f"  • Foreign key '{constraint_name}' already exists")

print("'tasks' table is ready.\n")

# --- COMPANIES TABLE ---
print("--- Setting up 'companies' table ---")
cur.execute("""
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
""")
print("'companies' table is ready.\n")

# Insert default companies
print("--- Adding default companies ---")
default_companies = ['Tabhi', 'Pranik.ai', 'Client A', 'Internal', 'Other']
for company in default_companies:
    cur.execute("""
        INSERT INTO companies (name) 
        VALUES (%s) 
        ON CONFLICT (name) DO NOTHING;
    """, (company,))
    print(f"  ✓ Company '{company}' ready")

# Commit all changes
conn.commit()
print("\n=== Database schema initialization complete! ===")

# Close the connection
cur.close()
conn.close()
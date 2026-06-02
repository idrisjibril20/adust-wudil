from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, hashlib, os, random, string
from functools import wraps

app = Flask(__name__)
app.secret_key = 'adustech_wudil_secret_2024'
DB = os.path.join(os.path.dirname(__file__), 'adustech.db')

# ── Database ──────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL DEFAULT 'student',
            campus_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            plate_number TEXT NOT NULL,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            color TEXT NOT NULL,
            year INTEGER,
            status TEXT DEFAULT 'pending',
            sticker_code TEXT,
            submitted_at TEXT DEFAULT (datetime('now')),
            approved_at TEXT,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS gate_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            checked_by INTEGER,
            direction TEXT DEFAULT 'in',
            note TEXT,
            logged_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY (checked_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_by INTEGER NOT NULL,
            assigned_to INTEGER,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            due_date TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS task_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (author_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')

    def add_user(name, email, pw, role, cid):
        h = hashlib.sha256(pw.encode()).hexdigest()
        try:
            c.execute("INSERT INTO users (full_name,email,password,role,campus_id) VALUES (?,?,?,?,?)",
                      (name, email, h, role, cid))
        except: pass

    add_user('Admin User',     'admin@adust.edu.ng',    'admin123',    'admin',    'ADM-001')
    add_user('Dr. Aminu Bello','staff@adust.edu.ng',    'staff123',    'staff',    'STF-042')
    add_user('Ibrahim Musa',   'student@adust.edu.ng',  'student123',  'student',  'STD-1021')
    add_user('Sec. Officer',   'security@adust.edu.ng', 'security123', 'security', 'SEC-007')

    try:
        c.execute("""INSERT INTO vehicles (owner_id,plate_number,make,model,color,year,status,sticker_code)
                     VALUES (3,'KN-234-ABC','Toyota','Corolla','Silver',2019,'approved','ADUS-2024-1021')""")
        c.execute("""INSERT INTO vehicles (owner_id,plate_number,make,model,color,year,status)
                     VALUES (2,'KN-101-XYZ','Honda','Accord','Black',2021,'pending')""")
    except: pass

    try:
        c.execute("""INSERT INTO tasks (title,description,created_by,assigned_to,priority,status,due_date)
                     VALUES ('Review parking policy','Update campus parking regulations for 2024',1,2,'high','open','2024-12-31')""")
        c.execute("""INSERT INTO tasks (title,description,created_by,assigned_to,priority,status,due_date)
                     VALUES ('Gate maintenance check','Inspect east gate barrier mechanism',1,4,'medium','in_progress','2024-11-30')""")
    except: pass

    conn.commit()
    conn.close()

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Auth helpers ──────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def dec(*a, **kw):
            if session.get('role') not in roles:
                flash('Access denied.', 'error')
                return redirect(url_for('dashboard'))
            return f(*a, **kw)
        return dec
    return decorator

def notify(user_id, msg):
    db = get_db()
    db.execute("INSERT INTO notifications (user_id,message) VALUES (?,?)", (user_id, msg))
    db.commit()
    db.close()

def unread_count():
    if 'user_id' not in session:
        return 0
    db = get_db()
    n = db.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0",
                   (session['user_id'],)).fetchone()[0]
    db.close()
    return n

# ── Auth routes ───────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pw    = hash_pw(request.form['password'])
        db    = get_db()
        user  = db.execute("SELECT * FROM users WHERE email=? AND password=?", (email, pw)).fetchone()
        db.close()
        if user:
            session['user_id']   = user['id']
            session['full_name'] = user['full_name']
            session['role']      = user['role']
            session['campus_id'] = user['campus_id']
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name  = request.form['full_name']
        email = request.form['email']
        pw    = hash_pw(request.form['password'])
        phone = request.form.get('phone', '')
        cid   = request.form.get('campus_id', '')
        role  = request.form.get('role', 'student')
        db    = get_db()
        try:
            db.execute("INSERT INTO users (full_name,email,password,phone,role,campus_id) VALUES (?,?,?,?,?,?)",
                       (name, email, pw, phone, role, cid))
            db.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Email already exists.', 'error')
        finally:
            db.close()
    return render_template('register.html')

# ── Dashboard ─────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    db   = get_db()
    uid  = session['user_id']
    role = session['role']
    stats = {}

    if role == 'admin':
        stats['Total Users']    = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        stats['Total Vehicles'] = db.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
        stats['Pending Reg']    = db.execute("SELECT COUNT(*) FROM vehicles WHERE status='pending'").fetchone()[0]
        stats['Open Tasks']     = db.execute("SELECT COUNT(*) FROM tasks WHERE status!='closed'").fetchone()[0]
        recent_vehicles = db.execute("""SELECT v.*, u.full_name FROM vehicles v
            JOIN users u ON v.owner_id=u.id ORDER BY v.submitted_at DESC LIMIT 5""").fetchall()
        recent_tasks = db.execute("""SELECT t.*, u.full_name as creator FROM tasks t
            JOIN users u ON t.created_by=u.id ORDER BY t.created_at DESC LIMIT 5""").fetchall()

    elif role == 'staff':
        stats['My Tasks']    = db.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to=?", (uid,)).fetchone()[0]
        stats['Open Tasks']  = db.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND status='open'", (uid,)).fetchone()[0]
        stats['Completed']   = db.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND status='closed'", (uid,)).fetchone()[0]
        stats['My Vehicles'] = db.execute("SELECT COUNT(*) FROM vehicles WHERE owner_id=?", (uid,)).fetchone()[0]
        recent_vehicles = db.execute("SELECT v.*, u.full_name FROM vehicles v JOIN users u ON v.owner_id=u.id WHERE v.owner_id=? ORDER BY v.submitted_at DESC LIMIT 5", (uid,)).fetchall()
        recent_tasks = db.execute("""SELECT t.*, u.full_name as creator FROM tasks t
            JOIN users u ON t.created_by=u.id WHERE t.assigned_to=? ORDER BY t.created_at DESC LIMIT 5""", (uid,)).fetchall()

    elif role == 'student':
        stats['My Vehicles'] = db.execute("SELECT COUNT(*) FROM vehicles WHERE owner_id=?", (uid,)).fetchone()[0]
        stats['Approved']    = db.execute("SELECT COUNT(*) FROM vehicles WHERE owner_id=? AND status='approved'", (uid,)).fetchone()[0]
        stats['Pending']     = db.execute("SELECT COUNT(*) FROM vehicles WHERE owner_id=? AND status='pending'", (uid,)).fetchone()[0]
        stats['My Tasks']    = db.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to=?", (uid,)).fetchone()[0]
        recent_vehicles = db.execute("SELECT v.*, u.full_name FROM vehicles v JOIN users u ON v.owner_id=u.id WHERE v.owner_id=? ORDER BY v.submitted_at DESC LIMIT 5", (uid,)).fetchall()
        recent_tasks = db.execute("SELECT t.*, u.full_name as creator FROM tasks t JOIN users u ON t.created_by=u.id WHERE t.assigned_to=? ORDER BY t.created_at DESC LIMIT 5", (uid,)).fetchall()

    else:  # security
        stats['Total Logs']  = db.execute("SELECT COUNT(*) FROM gate_logs").fetchone()[0]
        stats['Today Logs']  = db.execute("SELECT COUNT(*) FROM gate_logs WHERE date(logged_at)=date('now')").fetchone()[0]
        stats['Approved V']  = db.execute("SELECT COUNT(*) FROM vehicles WHERE status='approved'").fetchone()[0]
        stats['Pending Reg'] = db.execute("SELECT COUNT(*) FROM vehicles WHERE status='pending'").fetchone()[0]
        recent_vehicles = db.execute("""SELECT v.*, u.full_name FROM vehicles v
            JOIN users u ON v.owner_id=u.id WHERE v.status='approved' ORDER BY v.submitted_at DESC LIMIT 5""").fetchall()
        recent_tasks = []

    notifs = db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (uid,)).fetchall()
    db.close()
    return render_template('dashboard.html', stats=stats,
                           recent_vehicles=recent_vehicles,
                           recent_tasks=recent_tasks,
                           notifs=notifs, unread=unread_count())

# ── Vehicles ──────────────────────────────────────────────
@app.route('/vehicles')
@login_required
def vehicles():
    db   = get_db()
    uid  = session['user_id']
    role = session['role']
    if role in ('admin', 'security'):
        rows = db.execute("""SELECT v.*, u.full_name, u.campus_id FROM vehicles v
                             JOIN users u ON v.owner_id=u.id ORDER BY v.submitted_at DESC""").fetchall()
    else:
        rows = db.execute("""SELECT v.*, u.full_name, u.campus_id FROM vehicles v
                             JOIN users u ON v.owner_id=u.id
                             WHERE v.owner_id=? ORDER BY v.submitted_at DESC""", (uid,)).fetchall()
    db.close()
    return render_template('vehicles.html', vehicles=rows, unread=unread_count())

@app.route('/vehicles/register', methods=['GET', 'POST'])
@login_required
def register_vehicle():
    if request.method == 'POST':
        db = get_db()
        db.execute("""INSERT INTO vehicles (owner_id,plate_number,make,model,color,year)
                      VALUES (?,?,?,?,?,?)""",
                   (session['user_id'], request.form['plate_number'],
                    request.form['make'], request.form['model'],
                    request.form['color'], request.form.get('year', 0)))
        db.commit()
        admin = db.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
        if admin:
            notify(admin['id'], f"New vehicle registration from {session['full_name']} - {request.form['plate_number']}")
        db.close()
        flash('Vehicle submitted for approval.', 'success')
        return redirect(url_for('vehicles'))
    return render_template('vehicle_form.html', unread=unread_count())

@app.route('/vehicles/<int:vid>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_vehicle(vid):
    code = 'ADUS-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    db = get_db()
    v  = db.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
    db.execute("UPDATE vehicles SET status='approved',sticker_code=?,approved_at=datetime('now') WHERE id=?", (code, vid))
    db.commit()
    notify(v['owner_id'], f"Your vehicle {v['plate_number']} has been approved! Sticker: {code}")
    db.close()
    flash('Vehicle approved and sticker issued.', 'success')
    return redirect(url_for('vehicles'))

@app.route('/vehicles/<int:vid>/reject', methods=['POST'])
@login_required
@role_required('admin')
def reject_vehicle(vid):
    db = get_db()
    v  = db.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
    db.execute("UPDATE vehicles SET status='rejected' WHERE id=?", (vid,))
    db.commit()
    notify(v['owner_id'], f"Your vehicle {v['plate_number']} registration was rejected. Please contact admin.")
    db.close()
    flash('Vehicle rejected.', 'error')
    return redirect(url_for('vehicles'))

# ── Gate ─────────────────────────────────────────────────
@app.route('/gate')
@login_required
@role_required('admin', 'security')
def gate():
    db = get_db()
    logs = db.execute("""SELECT gl.*, v.plate_number, v.make, v.model, v.sticker_code,
                         u.full_name as owner, s.full_name as officer
                         FROM gate_logs gl
                         JOIN vehicles v ON gl.vehicle_id=v.id
                         JOIN users u ON v.owner_id=u.id
                         LEFT JOIN users s ON gl.checked_by=s.id
                         ORDER BY gl.logged_at DESC LIMIT 50""").fetchall()
    approved = db.execute("""SELECT v.*, u.full_name FROM vehicles v
                             JOIN users u ON v.owner_id=u.id WHERE v.status='approved'""").fetchall()
    db.close()
    return render_template('gate.html', logs=logs, vehicles=approved, unread=unread_count())

@app.route('/gate/log', methods=['POST'])
@login_required
@role_required('admin', 'security')
def log_gate():
    vid       = request.form['vehicle_id']
    direction = request.form.get('direction', 'in')
    note      = request.form.get('note', '')
    db = get_db()
    v  = db.execute("SELECT * FROM vehicles WHERE id=?", (vid,)).fetchone()
    if not v or v['status'] != 'approved':
        flash('Vehicle not found or not approved.', 'error')
        db.close()
        return redirect(url_for('gate'))
    db.execute("INSERT INTO gate_logs (vehicle_id,checked_by,direction,note) VALUES (?,?,?,?)",
               (vid, session['user_id'], direction, note))
    db.commit()
    notify(v['owner_id'], f"Your vehicle {v['plate_number']} was logged {direction.upper()} at the gate.")
    db.close()
    flash(f"Entry logged: {v['plate_number']} - {direction.upper()}", 'success')
    return redirect(url_for('gate'))

# ── Tasks ─────────────────────────────────────────────────
@app.route('/tasks')
@login_required
def tasks():
    db   = get_db()
    uid  = session['user_id']
    role = session['role']
    if role == 'admin':
        rows = db.execute("""SELECT t.*, c.full_name as creator, a.full_name as assignee
                             FROM tasks t JOIN users c ON t.created_by=c.id
                             LEFT JOIN users a ON t.assigned_to=a.id
                             ORDER BY t.created_at DESC""").fetchall()
    else:
        rows = db.execute("""SELECT t.*, c.full_name as creator, a.full_name as assignee
                             FROM tasks t JOIN users c ON t.created_by=c.id
                             LEFT JOIN users a ON t.assigned_to=a.id
                             WHERE t.created_by=? OR t.assigned_to=?
                             ORDER BY t.created_at DESC""", (uid, uid)).fetchall()
    staff = db.execute("SELECT id,full_name FROM users WHERE role IN ('staff','admin')").fetchall()
    db.close()
    return render_template('tasks.html', tasks=rows, staff=staff, unread=unread_count())

@app.route('/tasks/create', methods=['POST'])
@login_required
def create_task():
    db       = get_db()
    assigned = request.form.get('assigned_to') or None
    db.execute("""INSERT INTO tasks (title,description,created_by,assigned_to,priority,due_date)
                  VALUES (?,?,?,?,?,?)""",
               (request.form['title'], request.form.get('description', ''),
                session['user_id'], assigned,
                request.form.get('priority', 'medium'),
                request.form.get('due_date') or None))
    db.commit()
    if assigned:
        notify(int(assigned), f"New task assigned to you: {request.form['title']}")
    db.close()
    flash('Task created.', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/<int:tid>/status', methods=['POST'])
@login_required
def update_task_status(tid):
    status = request.form['status']
    db = get_db()
    db.execute("UPDATE tasks SET status=?,updated_at=datetime('now') WHERE id=?", (status, tid))
    db.commit()
    db.close()
    flash('Task updated.', 'success')
    return redirect(url_for('task_detail', tid=tid))

@app.route('/tasks/<int:tid>')
@login_required
def task_detail(tid):
    db = get_db()
    t  = db.execute("""SELECT t.*, c.full_name as creator, a.full_name as assignee
                       FROM tasks t JOIN users c ON t.created_by=c.id
                       LEFT JOIN users a ON t.assigned_to=a.id
                       WHERE t.id=?""", (tid,)).fetchone()
    comments = db.execute("""SELECT tc.*, u.full_name FROM task_comments tc
                             JOIN users u ON tc.author_id=u.id
                             WHERE tc.task_id=? ORDER BY tc.created_at""", (tid,)).fetchall()
    staff = db.execute("SELECT id,full_name FROM users WHERE role IN ('staff','admin')").fetchall()
    db.close()
    return render_template('task_detail.html', task=t, comments=comments, staff=staff, unread=unread_count())

@app.route('/tasks/<int:tid>/comment', methods=['POST'])
@login_required
def add_comment(tid):
    body = request.form['body']
    db   = get_db()
    db.execute("INSERT INTO task_comments (task_id,author_id,body) VALUES (?,?,?)",
               (tid, session['user_id'], body))
    t = db.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    if t['assigned_to'] and t['assigned_to'] != session['user_id']:
        notify(t['assigned_to'], f"New comment on task: {t['title']}")
    db.commit()
    db.close()
    return redirect(url_for('task_detail', tid=tid))

# ── Users ─────────────────────────────────────────────────
@app.route('/users')
@login_required
@role_required('admin')
def users():
    db   = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('users.html', users=rows, unread=unread_count())

# ── Notifications ─────────────────────────────────────────
@app.route('/notifications/read', methods=['POST'])
@login_required
def mark_read():
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session['user_id'],))
    db.commit()
    db.close()
    return jsonify({'ok': True})

# ── Run ───────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

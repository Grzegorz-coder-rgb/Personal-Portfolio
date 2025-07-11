# your_project/main.py (CAŁA ZAWARTOŚĆ PLIKU)

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Course, Module, Lesson, UserCourseAccess # Importuj instancję db i wszystkie modele
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

import os

app = Flask(__name__)

# Konfiguracja bazy danych SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# ZMIEN TO NA SWÓJ SEKRETNY KLUCZ! Użyj czegoś bezpiecznego, np. os.urandom(24).hex()
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key_change_me_in_production_xyz123')

# Utwórz folder 'instance' jeśli nie istnieje (potrzebne dla SQLite w app.instance_path)
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# === WAŻNE: Zainicjuj 'db' z 'app' TYLKO RAZ i PRZED Użyciem Modeli SQLAlchemy ===
db.init_app(app)

# === Funkcja do inicjalizacji bazy danych i dodawania przykładowych danych ===
def init_db_and_data():
    with app.app_context():
        db.create_all() # Tworzy tabele, jeśli nie istnieją

        if not User.query.first(): # Sprawdź, czy są jacyś użytkownicy
            print("Dodawanie przykładowych danych...")

            admin_email = "grzegorzgladysz2204@gmail.com"
            admin_password = "Lego2012"

            admin_user = User(username='admin', email=admin_email, lessons_balance=100, role='admin')
            admin_user.password_hash = generate_password_hash(admin_password) # Użyj generate_password_hash
            db.session.add(admin_user)
            db.session.commit() # Zatwierdź admina, aby otrzymał ID

            # --- Definiowanie Kursów ---
            courses_data = [
                {
                    'name': 'Python Dev',
                    'description': 'Kompleksowy kurs programowania w Pythonie od podstaw.',
                    'gradient_class': 'course-gradient-python',
                    'modules': [
                        {'name': 'Moduł 1: Podstawy Pythona', 'gradient_class': 'module-gradient-1', 'lessons_count': 4},
                        {'name': 'Moduł 2: Struktury Danych', 'gradient_class': 'module-gradient-2', 'lessons_count': 4},
                        {'name': 'Moduł 3: Funkcje i Moduły', 'gradient_class': 'module-gradient-3', 'lessons_count': 4},
                        {'name': 'Moduł 4: Programowanie Obiektowe', 'gradient_class': 'module-gradient-4', 'lessons_count': 4},
                        {'name': 'Moduł 5: Obsługa Plików i Wyjątków', 'gradient_class': 'module-gradient-5', 'lessons_count': 4},
                        {'name': 'Moduł 6: Web Scraping i API', 'gradient_class': 'module-gradient-6', 'lessons_count': 4},
                        {'name': 'Moduł 7: Bazy Danych z Pythonem', 'gradient_class': 'module-gradient-7', 'lessons_count': 4},
                        {'name': 'Moduł 8: Wprowadzenie do Flask', 'gradient_class': 'module-gradient-8', 'lessons_count': 4}
                    ]
                },
                {
                    'name': 'Full Stack',
                    'description': 'Kompleksowy kurs tworzenia pełnych aplikacji webowych.',
                    'gradient_class': 'course-gradient-fullstack',
                    'modules': [
                        {'name': 'FS Moduł 1: Wprowadzenie do Frontend', 'gradient_class': 'module-gradient-fullstack-1', 'lessons_count': 4},
                        {'name': 'FS Moduł 2: CSS Zaawansowany', 'gradient_class': 'module-gradient-fullstack-2', 'lessons_count': 4},
                        {'name': 'FS Moduł 3: JavaScript ES6+', 'gradient_class': 'module-gradient-fullstack-3', 'lessons_count': 4},
                        {'name': 'FS Moduł 4: React.js Podstawy', 'gradient_class': 'module-gradient-fullstack-4', 'lessons_count': 4},
                        {'name': 'FS Moduł 5: Node.js i Express', 'gradient_class': 'module-gradient-fullstack-5', 'lessons_count': 4},
                        {'name': 'FS Moduł 6: Bazy Danych NoSQL', 'gradient_class': 'module-gradient-fullstack-6', 'lessons_count': 4},
                        {'name': 'FS Moduł 7: RESTful API', 'gradient_class': 'module-gradient-fullstack-7', 'lessons_count': 4},
                        {'name': 'FS Moduł 8: Deployment i CI/CD', 'gradient_class': 'module-gradient-fullstack-8', 'lessons_count': 4}
                    ]
                },
                {
                    'name': 'AI & ML Dev',
                    'description': 'Kurs wprowadzający do sztucznej inteligencji i uczenia maszynowego.',
                    'gradient_class': 'course-gradient-aiml',
                    'modules': [
                        {'name': 'AI/ML Moduł 1: Wprowadzenie do AI/ML', 'gradient_class': 'module-gradient-aiml-1', 'lessons_count': 4},
                        {'name': 'AI/ML Moduł 2: Podstawy Pythona dla ML', 'gradient_class': 'module-gradient-aiml-2', 'lessons_count': 4},
                        {'name': 'AI/ML Moduł 3: Statystyka i Prawdopodobieństwo', 'gradient_class': 'module-gradient-aiml-3', 'lessons_count': 4},
                        {'name': 'AI/ML Moduł 4: Uczenie Nadzorowane', 'gradient_class': 'module-gradient-aiml-4', 'lessons_count': 4},
                        {'name': 'AI/ML Moduł 5: Uczenie Nienadzorowane', 'gradient_class': 'module-gradient-aiml-5', 'lessons_count': 4},
                        {'name': 'AI/ML Moduł 6: Sieci Neuronowe i Deep Learning', 'gradient_class': 'module-gradient-aiml-6', 'lessons_count': 4},
                        {'name': 'AI/ML Moduł 7: Przetwarzanie Języka Naturalnego (NLP)', 'gradient_class': 'module-gradient-aiml-7', 'lessons_count': 4},
                        {'name': 'AI/ML Moduł 8: Wizja Komputerowa', 'gradient_class': 'module-gradient-aiml-8', 'lessons_count': 4}
                    ]
                },
                {
                    'name': 'Frontend Dev',
                    'description': 'Kurs skupiający się na tworzeniu interfejsów użytkownika.',
                    'gradient_class': 'course-gradient-frontend',
                    'modules': [
                        {'name': 'FE Moduł 1: HTML5 i CSS3', 'gradient_class': 'module-gradient-frontend-1', 'lessons_count': 4},
                        {'name': 'FE Moduł 2: Responsywny Design', 'gradient_class': 'module-gradient-frontend-2', 'lessons_count': 4},
                        {'name': 'FE Moduł 3: Zaawansowany CSS i Animacje', 'gradient_class': 'module-gradient-frontend-3', 'lessons_count': 4},
                        {'name': 'FE Moduł 4: JavaScript od Podstaw', 'gradient_class': 'module-gradient-frontend-4', 'lessons_count': 4},
                        {'name': 'FE Moduł 5: DOM Manipulation', 'gradient_class': 'module-gradient-frontend-5', 'lessons_count': 4},
                        {'name': 'FE Moduł 6: Asynchroniczny JavaScript', 'gradient_class': 'module-gradient-frontend-6', 'lessons_count': 4},
                        {'name': 'FE Moduł 7: React Podstawy', 'gradient_class': 'module-gradient-frontend-7', 'lessons_count': 4},
                        {'name': 'FE Moduł 8: Narzędzia Frontendowe', 'gradient_class': 'module-gradient-frontend-8', 'lessons_count': 4}
                    ]
                },
            ]

            all_courses_in_db = []
            for c_data in courses_data:
                total_lessons_in_course = sum(m['lessons_count'] for m in c_data['modules'])
                course = Course(
                    name=c_data['name'],
                    description=c_data['description'],
                    gradient_class=c_data['gradient_class'],
                    total_lessons=total_lessons_in_course # Ustawiamy total_lessons dla kursu
                )
                db.session.add(course)
                db.session.commit() # Zatwierdź kurs, aby otrzymał ID
                all_courses_in_db.append(course)

                for i, m_data in enumerate(c_data['modules']):
                    module = Module(
                        course_id=course.id,
                        name=m_data['name'], # Używamy 'name' dla modułu
                        order=i + 1,
                        total_lessons=m_data['lessons_count'], # Ustawiamy total_lessons dla modułu
                        gradient_class=m_data['gradient_class']
                    )
                    db.session.add(module)
                    db.session.commit() # Zatwierdź moduł, aby otrzymał ID

                    # Dodaj lekcje do każdego modułu
                    for j in range(1, m_data['lessons_count'] + 1):
                        lesson = Lesson(
                            module_id=module.id,
                            name=f'Lekcja {module.order}.{j}: Temat Lekcji {j}',
                            content=f'To jest treść lekcji {module.order}.{j} dla modułu "{module.name}" w kursie "{course.name}".',
                            order=j
                        )
                        db.session.add(lesson)
            db.session.commit() # Zatwierdź wszystkie lekcje i moduły na raz

            # Przypisz wszystkie kursy do użytkownika admina
            for course_obj in all_courses_in_db:
                user_course_access = UserCourseAccess(user_id=admin_user.id, course_id=course_obj.id, lessons_completed=0)
                db.session.add(user_course_access)
            db.session.commit()
            print("Przykładowe dane dodane.")
        else:
            print("Baza danych już zawiera dane. Jeśli chcesz ją zresetować, usuń plik 'site.db' w folderze 'instance'.")


# === Funkcje pomocnicze (Dekoratory) ===

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['logged_in']:
            return f(*args, **kwargs)
        else:
            flash('Musisz się zalogować, aby uzyskać dostęp do tej strony.', 'danger')
            return redirect(url_for('login'))
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['logged_in'] and session.get('user_role') == 'admin':
            return f(*args, **kwargs)
        else:
            flash('Brak uprawnień. Tylko administratorzy mogą uzyskać dostęp do tej strony.', 'danger')
            return redirect(url_for('index'))
    return wrap

# === Flask Routes ===

# Strona główna (Twoje portfolio)
@app.route('/')
def index():
    login_url = url_for('login')
    learn_url = url_for('learn') if 'user_id' in session else url_for('login')
    return render_template('index.html', login_url=login_url, learn_url=learn_url)

# Logowanie
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('learn'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['logged_in'] = True
            session['username'] = user.username
            session['user_id'] = user.id
            session['user_role'] = user.role
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('learn'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')
    return render_template('login.html')
    if 'user_id' in session:
        return redirect(url_for('learn'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not username or not email or not password:
            flash('Wszystkie pola są wymagane!', 'error')
            return render_template('register.html')

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Nazwa użytkownika jest już zajęta.', 'error')
        elif existing_email:
            flash('Ten adres e-mail jest już zarejestrowany.', 'error')
        else:
            new_user = User(username=username, email=email, role='user') # Nowi użytkownicy domyślnie mają rolę 'user'
            new_user.password_hash = generate_password_hash(password)
            db.session.add(new_user)
            db.session.commit()

            # Przypisanie wszystkich kursów nowemu użytkownikowi (możesz to zmienić na konkretne kursy)
            all_courses = Course.query.all()
            for course_obj in all_courses:
                user_course_access = UserCourseAccess(user_id=new_user.id, course_id=course_obj.id, lessons_completed=0)
                db.session.add(user_course_access)
            db.session.commit()

            flash('Konto utworzone pomyślnie! Możesz się zalogować.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Wylogowanie
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('user_role', None)
    session.pop('logged_in', None) # Upewnij się, że 'logged_in' też jest czyszczone
    flash('Zostałeś wylogowany.', 'info')
    return redirect(url_for('login'))

# Panel nauki (learn.html)
@app.route('/learn')
@is_logged_in # Upewnij się, że użytkownik jest zalogowany
def learn():
    user_id = session['user_id']
    current_user = User.query.get(user_id)

    if not current_user:
        flash('Użytkownik nie znaleziony.', 'error')
        return redirect(url_for('logout'))

    user_courses_data = []
    user_courses_relationships = UserCourseAccess.query.filter_by(user_id=user_id).all()

    for uc_rel in user_courses_relationships:
        course = Course.query.get(uc_rel.course_id)
        if course:
            modules_data = []
            course_global_lessons_count = 0
            for module in sorted(course.modules, key=lambda m: m.order):
                lessons_in_module = Lesson.query.filter_by(module_id=module.id).count()
                
                module_start_global_index = course_global_lessons_count
                lessons_completed_in_module = max(0, min(lessons_in_module, uc_rel.lessons_completed - module_start_global_index))
                
                module_status = "not_started"
                if lessons_in_module > 0 and lessons_completed_in_module == lessons_in_module:
                    module_status = "completed"
                elif lessons_completed_in_module > 0 and lessons_completed_in_module < lessons_in_module:
                    module_status = "in_progress"

                lessons_for_module = Lesson.query.filter_by(module_id=module.id).order_by(Lesson.order).all()
                module_lessons_list = []
                for lesson in lessons_for_module:
                    module_lessons_list.append({
                        "id": lesson.id,
                        "name": lesson.name,
                        "order": lesson.order,
                        "content": lesson.content
                    })

                modules_data.append({
                    "id": module.id,
                    "title": module.name,
                    "lessons_completed": lessons_completed_in_module,
                    "total_lessons": lessons_in_module,
                    "status": module_status,
                    "gradient_class": module.gradient_class,
                    "lessons_list": module_lessons_list
                })
                course_global_lessons_count += lessons_in_module

            course_progress_percent = 0
            if course.total_lessons > 0:
                course_progress_percent = (uc_rel.lessons_completed / course.total_lessons) * 100

            user_courses_data.append({
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "gradient_class": course.gradient_class,
                "progress_lessons_completed": uc_rel.lessons_completed,
                "progress_total_lessons": course.total_lessons,
                "progress_percent": int(course_progress_percent),
                "modules": modules_data,
                "tabs": ["Na lekcji", "Zadanie domowe", "Ocena"],
                "current_lesson_id": uc_rel.current_lesson_id
            })

    active_course_id = request.args.get('course_id')
    active_course = None
    if active_course_id:
        for course_data in user_courses_data:
            if str(course_data['id']) == active_course_id:
                active_course = course_data
                break

    if not active_course and user_courses_data:
        active_course = user_courses_data[0]

    active_lesson_content = "Wybierz lekcję, aby zobaczyć jej zawartość."
    active_lesson_name = "Brak wybranej lekcji"

    if active_course and active_course['current_lesson_id']:
        for module in active_course['modules']:
            for lesson in module['lessons_list']:
                if lesson['id'] == active_course['current_lesson_id']:
                    active_lesson_content = lesson['content']
                    active_lesson_name = lesson['name']
                    break
            if active_lesson_content != "Wybierz lekcję, aby zobaczyć jej zawartość.":
                break
    elif active_course and active_course['modules']:
        if active_course['modules'][0]['lessons_list']:
            first_lesson = active_course['modules'][0]['lessons_list'][0]
            active_lesson_content = first_lesson['content']
            active_lesson_name = first_lesson['name']
            with app.app_context():
                uc_rel_to_update = UserCourseAccess.query.filter_by(user_id=user_id, course_id=active_course['id']).first()
                if uc_rel_to_update:
                    uc_rel_to_update.current_lesson_id = first_lesson['id']
                    db.session.commit()

    return render_template(
        'learn.html',
        user_courses=user_courses_data,
        active_course=active_course,
        username=current_user.username,
        lessons_balance=current_user.lessons_balance,
        active_lesson_content=active_lesson_content,
        active_lesson_name=active_lesson_name,
        current_user=current_user # <--- WAŻNE: DODAJ TĘ LINIĘ
    )

# Trasa do aktualizacji bieżącej lekcji użytkownika w danym kursie
@app.route('/update_current_lesson', methods=['POST'])
def update_current_lesson():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    course_id = request.json.get('course_id')
    lesson_id = request.json.get('lesson_id')

    if not course_id or not lesson_id:
        return jsonify({'status': 'error', 'message': 'Missing course_id or lesson_id'}), 400

    user_course_access = UserCourseAccess.query.filter_by(user_id=user_id, course_id=course_id).first()
    if user_course_access:
        user_course_access.current_lesson_id = lesson_id

        current_lesson_obj = Lesson.query.get(lesson_id)
        if current_lesson_obj:
            course = Course.query.get(course_id)
            
            lessons_in_course_ordered = []
            for module in sorted(course.modules, key=lambda m: m.order):
                lessons_in_course_ordered.extend(sorted(module.lessons, key=lambda l: l.order))

            lesson_global_order = -1
            for i, l in enumerate(lessons_in_course_ordered):
                if l.id == lesson_id:
                    lesson_global_order = i + 1
                    break
            
            if lesson_global_order != -1:
                # Zwiększ lessons_completed tylko jeśli nowa lekcja ma wyższy porządek
                # i upewnij się, że nie przekracza całkowitej liczby lekcji w kursie
                if user_course_access.lessons_completed < lesson_global_order:
                    user_course_access.lessons_completed = min(lesson_global_order, course.total_lessons)

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Current lesson updated'})
    return jsonify({'status': 'error', 'message': 'User course not found'}), 404

# Pozostałe trasy (bez zmian w stosunku do poprzedniej wersji)
@app.route("/hire")
def hire():
    return render_template("hire.html")

@app.route("/projects")
def projects():
    return render_template("projects.html")

@app.route("/plan")
def plan():
    return render_template("plan.html")

@app.route("/python")
def python():
    return render_template("python.html")

@app.route("/fullstack")
def full():
    return render_template("full.html")

@app.route("/frontend")
def frontend():
    return render_template("frontend.html")

@app.route("/backend")
def backend():
    return render_template("backend.html")

@app.route("/AI")
def AI():
    return render_template("AI.html")

# --- ADMIN PANEL ROUTES ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_lessons = Lesson.query.count()
    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_courses=total_courses,
                           total_lessons=total_lessons)

# --- Zarządzanie Użytkownikami ---
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        lessons_balance = int(request.form.get('lessons_balance', 0))

        if User.query.filter_by(username=username).first():
            flash('Nazwa użytkownika już istnieje!', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email już istnieje!', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=hashed_password,
                            role=role, lessons_balance=lessons_balance)
            db.session.add(new_user)
            db.session.commit()
            flash('Użytkownik dodany pomyślnie!', 'success')
            return redirect(url_for('admin_users'))
    return render_template('admin/add_user.html')

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']
        user.lessons_balance = int(request.form['lessons_balance'])
        if request.form['password']:
            user.password_hash = generate_password_hash(request.form['password'])
        db.session.commit()
        flash('Użytkownik zaktualizowany pomyślnie!', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Usuń powiązane UserCourseAccess przed usunięciem użytkownika (kaskadowe usuwanie w models.py powinno to zrobić, ale to jest bezpieczniejsze)
    UserCourseAccess.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash('Użytkownik usunięty pomyślnie!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/assign_course/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_assign_course_to_user(user_id):
    user = User.query.get_or_404(user_id)
    all_courses = Course.query.all()
    user_assigned_course_ids = [uc.course_id for uc in user.course_accesses]

    if request.method == 'POST':
        course_id_to_assign = request.form.get('course_id')
        if course_id_to_assign:
            course_id_to_assign = int(course_id_to_assign)
            existing_access = UserCourseAccess.query.filter_by(user_id=user.id, course_id=course_id_to_assign).first()
            if not existing_access:
                new_access = UserCourseAccess(user_id=user.id, course_id=course_id_to_assign, lessons_completed=0, current_lesson_id=None)
                db.session.add(new_access)
                db.session.commit()
                flash(f'Dostęp do kursu {Course.query.get(course_id_to_assign).name} nadany użytkownikowi {user.username}.', 'success')
            else:
                flash(f'Użytkownik {user.username} już ma dostęp do tego kursu.', 'warning')
        else:
            flash('Wybierz kurs do przypisania.', 'danger')
        return redirect(url_for('admin_assign_course_to_user', user_id=user.id))

    return render_template('admin/assign_course_to_user.html',
                           user=user,
                           all_courses=all_courses,
                           user_assigned_course_ids=user_assigned_course_ids)

@app.route('/admin/users/revoke_course/<int:user_id>/<int:course_id>', methods=['POST'])
@admin_required
def admin_revoke_course_from_user(user_id, course_id):
    user_course_access = UserCourseAccess.query.filter_by(user_id=user_id, course_id=course_id).first_or_404()
    user = User.query.get(user_id)
    course = Course.query.get(course_id)
    db.session.delete(user_course_access)
    db.session.commit()
    flash(f'Dostęp do kursu {course.name} odebrany użytkownikowi {user.username}.', 'info')
    return redirect(url_for('admin_assign_course_to_user', user_id=user.id))

# --- Zarządzanie Kursami ---
@app.route('/admin/courses')
@admin_required
def admin_courses():
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses)

@app.route('/admin/courses/add', methods=['GET', 'POST'])
@admin_required
def admin_add_course():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        gradient_class = request.form.get('gradient_class', 'course-gradient-default')
        new_course = Course(name=name, description=description, gradient_class=gradient_class, total_lessons=0)
        db.session.add(new_course)
        db.session.commit()
        flash('Kurs dodany pomyślnie!', 'success')
        return redirect(url_for('admin_courses'))
    return render_template('admin/add_course.html')

@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'POST':
        course.name = request.form['name']
        course.description = request.form['description']
        course.gradient_class = request.form.get('gradient_class', 'course-gradient-default')
        db.session.commit()
        flash('Kurs zaktualizowany pomyślnie!', 'success')
        return redirect(url_for('admin_courses'))
    return render_template('admin/edit_course.html', course=course)

@app.route('/admin/courses/delete/<int:course_id>', methods=['POST'])
@admin_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    # Usuń powiązane UserCourseAccess, moduły i lekcje
    UserCourseAccess.query.filter_by(course_id=course.id).delete()
    for module in course.modules:
        Lesson.query.filter_by(module_id=module.id).delete()
    Module.query.filter_by(course_id=course.id).delete()
    
    db.session.delete(course)
    db.session.commit()
    flash('Kurs usunięty pomyślnie!', 'success')
    return redirect(url_for('admin_courses'))

# --- Zarządzanie Modułami ---
@app.route('/admin/modules')
@admin_required
def admin_modules():
    modules = Module.query.order_by(Module.course_id, Module.order).all()
    courses = Course.query.all()
    return render_template('admin/modules.html', modules=modules, courses=courses)

@app.route('/admin/modules/add', methods=['GET', 'POST'])
@admin_required
def admin_add_module():
    courses = Course.query.all()
    if request.method == 'POST':
        name = request.form['name'] # Zmieniono z 'title' na 'name'
        order = int(request.form['order'])
        course_id = int(request.form['course_id'])
        gradient_class = request.form.get('gradient_class', 'module-gradient-default')
        new_module = Module(name=name, order=order, course_id=course_id, gradient_class=gradient_class, total_lessons=0)
        db.session.add(new_module)
        db.session.commit()

        # Zaktualizuj total_lessons w Course po dodaniu modułu
        course = Course.query.get(course_id)
        if course:
            course.total_lessons = sum(m.total_lessons for m in course.modules)
            db.session.commit()

        flash('Moduł dodany pomyślnie!', 'success')
        return redirect(url_for('admin_modules'))
    return render_template('admin/add_module.html', courses=courses)

@app.route('/admin/modules/edit/<int:module_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_module(module_id):
    module = Module.query.get_or_404(module_id)
    courses = Course.query.all()
    if request.method == 'POST':
        old_course_id = module.course_id # Zapamiętaj stary kurs, jeśli moduł zostanie przeniesiony
        module.name = request.form['name'] # Zmieniono z 'title' na 'name'
        module.order = int(request.form['order'])
        module.course_id = int(request.form['course_id'])
        module.gradient_class = request.form.get('gradient_class', 'module-gradient-default')
        db.session.commit()

        # Zaktualizuj total_lessons w kursach, jeśli moduł został przeniesiony
        if old_course_id != module.course_id:
            old_course = Course.query.get(old_course_id)
            if old_course:
                old_course.total_lessons = sum(m.total_lessons for m in old_course.modules)
                db.session.commit()
        
        new_course = Course.query.get(module.course_id)
        if new_course:
            new_course.total_lessons = sum(m.total_lessons for m in new_course.modules)
            db.session.commit()

        flash('Moduł zaktualizowany pomyślnie!', 'success')
        return redirect(url_for('admin_modules'))
    return render_template('admin/edit_module.html', module=module, courses=courses)

@app.route('/admin/modules/delete/<int:module_id>', methods=['POST'])
@admin_required
def admin_delete_module(module_id):
    module = Module.query.get_or_404(module_id)
    course_id = module.course_id # Zapamiętaj ID kursu, aby zaktualizować total_lessons
    
    # Usuń powiązane lekcje przed usunięciem modułu
    Lesson.query.filter_by(module_id=module.id).delete()
    db.session.delete(module)
    db.session.commit()

    # Zaktualizuj total_lessons w Course
    course = Course.query.get(course_id)
    if course:
        course.total_lessons = sum(m.total_lessons for m in course.modules)
        db.session.commit()

    flash('Moduł usunięty pomyślnie!', 'success')
    return redirect(url_for('admin_modules'))

# --- Zarządzanie Lekcjami ---
@app.route('/admin/lessons')
@admin_required
def admin_lessons():
    lessons = Lesson.query.order_by(Lesson.module_id, Lesson.order).all()
    modules = Module.query.all()
    return render_template('admin/lessons.html', lessons=lessons, modules=modules)

@app.route('/admin/lessons/add', methods=['GET', 'POST'])
@admin_required
def admin_add_lesson():
    modules = Module.query.all()
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        order = int(request.form['order'])
        module_id = int(request.form['module_id'])
        new_lesson = Lesson(name=name, content=content, order=order, module_id=module_id)
        db.session.add(new_lesson)
        db.session.commit()

        # Zaktualizuj total_lessons w Module i Course
        module = Module.query.get(module_id)
        if module:
            module.total_lessons = Lesson.query.filter_by(module_id=module_id).count()
            db.session.commit()
            if module.course:
                course = module.course
                course.total_lessons = sum(m.total_lessons for m in course.modules)
                db.session.commit()

        flash('Lekcja dodana pomyślnie!', 'success')
        return redirect(url_for('admin_lessons'))
    return render_template('admin/add_lesson.html', modules=modules)

@app.route('/admin/lessons/edit/<int:lesson_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    modules = Module.query.all()
    if request.method == 'POST':
        old_module_id = lesson.module_id
        lesson.name = request.form['name']
        lesson.content = request.form['content']
        lesson.order = int(request.form['order'])
        lesson.module_id = int(request.form['module_id'])
        db.session.commit()

        # Zaktualizuj total_lessons w modułach i kursach
        if old_module_id != lesson.module_id:
            old_module = Module.query.get(old_module_id)
            if old_module:
                old_module.total_lessons = Lesson.query.filter_by(module_id=old_module_id).count()
                db.session.commit()
                if old_module.course:
                    old_module.course.total_lessons = sum(m.total_lessons for m in old_module.course.modules)
                    db.session.commit()
        
        new_module = Module.query.get(lesson.module_id)
        if new_module:
            new_module.total_lessons = Lesson.query.filter_by(module_id=lesson.module_id).count()
            db.session.commit()
            if new_module.course:
                new_module.course.total_lessons = sum(m.total_lessons for m in new_module.course.modules)
                db.session.commit()

        flash('Lekcja zaktualizowana pomyślnie!', 'success')
        return redirect(url_for('admin_lessons'))
    return render_template('admin/edit_lesson.html', lesson=lesson, modules=modules)

@app.route('/admin/lessons/delete/<int:lesson_id>', methods=['POST'])
@admin_required
def admin_delete_lesson(lesson_id):

    lesson = Lesson.query.get_or_404(lesson_id)
    module_id = lesson.module_id
    db.session.delete(lesson)
    db.session.commit()

    # Zaktualizuj total_lessons w Module i Course
    module = Module.query.get(module_id)
    if module:
        module.total_lessons = Lesson.query.filter_by(module_id=module_id).count()
        db.session.commit()
        if module.course:
            course = module.course
            course.total_lessons = sum(m.total_lessons for m in course.modules)
            db.session.commit()

    flash('Lekcja usunięta pomyślnie!', 'success')
    return redirect(url_for('admin_lessons'))

@app.route('/enroll/<string:course_name>')
@is_logged_in # Upewnij się, że użytkownik jest zalogowany
def enroll_course(course_name):
    user_id = session['user_id']
    user = User.query.get(user_id)
    course = Course.query.filter_by(name=course_name).first()

    if not user:
        flash('Musisz być zalogowany, aby zapisać się na kurs.', 'warning')
        return redirect(url_for('login'))

    if not course:
        flash('Kurs o podanej nazwie nie istnieje.', 'error')
        return redirect(url_for('learn')) # Przekieruj do strony nauki, jeśli kurs nie znaleziony

    # Sprawdź, czy użytkownik już jest zapisany na ten kurs
    existing_access = UserCourseAccess.query.filter_by(user_id=user.id, course_id=course.id).first()

    if existing_access:
        flash(f'Jesteś już zapisany na kurs "{course.name}".', 'info')
    else:
        # Tworzenie nowego rekordu dostępu użytkownika do kursu
        new_access = UserCourseAccess(user_id=user.id, course_id=course.id, lessons_completed=0, current_lesson_id=None)
        db.session.add(new_access)
        db.session.commit()
        flash(f'Pomyślnie zapisano na kurs "{course.name}"!', 'success')

    # Po zapisaniu (lub jeśli już był zapisany), przekieruj użytkownika do strony nauki dla tego kursu
    return redirect(url_for('learn', course_id=course.id))

# === Uruchomienie aplikacji Flask ===
if __name__ == '__main__':
    # Ta sekcja zostanie uruchomiona tylko wtedy, gdy plik main.py jest uruchamiany bezpośrednio
    # a nie importowany jako moduł.
    init_db_and_data() # Wywołanie funkcji do inicjalizacji bazy danych i dodania danych
    app.run(debug=True) # Uruchom aplikację w trybie debugowania
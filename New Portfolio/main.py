# app.py
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib # Do prostego hashowania hasła

app = Flask(__name__)

# Konfiguracja bazy danych SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'twoj_bardzo_tajny_klucz_tutaj_zmien_go_na_cos_silnego' # ZMIEN TO!

db = SQLAlchemy(app)

# Utwórz folder 'instance' jeśli nie istnieje
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# === UPROSZCZONA FUNKCJA HASZOWANIA I SPRAWDZANIA HASŁA BEZ WERKZEUG (NIEBEZPIECZNE W PRODUKCJI) ===
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16) # Generuj losową sól
    salted_password = salt + password.encode('utf-8')
    return salt + hashlib.sha256(salted_password).digest()

def check_password(hashed_password, password):
    salt = hashed_password[:16]
    stored_hash = hashed_password[16:]
    salted_password = salt + password.encode('utf-8')
    return stored_hash == hashlib.sha256(salted_password).digest()
# ===================================================================================================

# === Modele Bazy Danych ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.LargeBinary, nullable=False) # Zmieniono na LargeBinary dla soli i hasha
    lessons_balance = db.Column(db.Integer, default=0) # Saldo lekcji
    courses = db.relationship('UserCourse', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return check_password(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    gradient_class = db.Column(db.String(50), nullable=False) # Klasa CSS dla gradientu
    total_lessons = db.Column(db.Integer, default=0) # Całkowita liczba lekcji w kursie
    modules = db.relationship('Module', backref='course', lazy=True)

    def __repr__(self):
        return f'<Course {self.name}>'

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    total_lessons = db.Column(db.Integer, default=0) # Całkowita liczba lekcji w module
    lessons = db.relationship('Lesson', backref='module', lazy=True)
    gradient_class = db.Column(db.String(50), nullable=False) # Klasa CSS dla gradientu modułu

    def __repr__(self):
        return f'<Module {self.name}>'

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text) # Treść lekcji
    order = db.Column(db.Integer, nullable=False) # Kolejność lekcji w module

    def __repr__(self):
        return f'<Lesson {self.name}>'

class UserCourse(db.Model):
    # Tabela łącząca użytkowników z kursami (zakupione kursy)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lessons_completed = db.Column(db.Integer, default=0) # Ile lekcji ukończył użytkownik w TYM kursie

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='_user_course_uc'),)

    def __repr__(self):
        return f'<User {self.user_id} - Course {self.course_id}>'

# === Funkcja do inicjalizacji bazy danych i dodawania przykładowych danych ===
def init_db_and_data():
    with app.app_context():
        # Ważne: Jeśli zmieniasz strukturę modelu User (np. z String na LargeBinary),
        # musisz usunąć starą bazę danych (site.db) lub użyć migracji (Alembic).
        # Dla tego zadania, najprościej jest usunąć plik site.db
        # usuń 'instance/site.db' jeśli istnieje przed pierwszym uruchomieniem
        # jeśli była wcześniej użyta biblioteka Werkzeug.security
        db.create_all() # Tworzy wszystkie tabele

        # Dodaj przykładowe dane, jeśli baza jest pusta
        if not User.query.first():
            print("Dodawanie przykładowych danych...")

            # Użytkownik Admin - TYLKO DLA CIEBIE
            admin_user = User(username='admin', email='admin@gregacademy.com', lessons_balance=100)
            admin_user.set_password('adminpass') # ZMIEN TO HASŁO NA SILNE!
            db.session.add(admin_user)

            # Kurs Python Programming Language
            python_course = Course(
                name='Python Programming Language',
                description='Kompleksowy kurs programowania w Pythonie od podstaw.',
                gradient_class='course-gradient-python',
                total_lessons=32
            )
            db.session.add(python_course)

            # Moduły do kursu Python
            mod1 = Module(course=python_course, name='Moduł 1: Podstawy Pythona', total_lessons=4, gradient_class='module-gradient-1')
            mod2 = Module(course=python_course, name='Moduł 2: Struktury Danych', total_lessons=4, gradient_class='module-gradient-2')
            mod3 = Module(course=python_course, name='Moduł 3: Funkcje i Moduły', total_lessons=5, gradient_class='module-gradient-3')
            mod4 = Module(course=python_course, name='Moduł 4: Programowanie Obiektowe', total_lessons=5, gradient_class='module-gradient-4')
            mod5 = Module(course=python_course, name='Moduł 5: Obsługa Plików i Wyjątków', total_lessons=6, gradient_class='module-gradient-5')
            db.session.add_all([mod1, mod2, mod3, mod4, mod5])

            # Lekcje do Modułu 1 (Python)
            lesson1_1 = Lesson(module=mod1, name='Wprowadzenie do Pythona', content='...', order=1)
            lesson1_2 = Lesson(module=mod1, name='Zmienne i Typy Danych', content='...', order=2)
            lesson1_3 = Lesson(module=mod1, name='Operatory', content='...', order=3)
            lesson1_4 = Lesson(module=mod1, name='Instrukcje Warunkowe', content='...', order=4)
            db.session.add_all([lesson1_1, lesson1_2, lesson1_3, lesson1_4])

            # Lekcje do Modułu 2 (Python)
            lesson2_1 = Lesson(module=mod2, name='Listy', content='...', order=1)
            lesson2_2 = Lesson(module=mod2, name='Krotki', content='...', order=2)
            lesson2_3 = Lesson(module=mod2, name='Zbiory', content='...', order=3)
            lesson2_4 = Lesson(module=mod2, name='Słowniki', content='...', order=4)
            db.session.add_all([lesson2_1, lesson2_2, lesson2_3, lesson2_4])

            # Lekcje do Modułu 3 (Python)
            lesson3_1 = Lesson(module=mod3, name='Definiowanie Funkcji', content='...', order=1)
            lesson3_2 = Lesson(module=mod3, name='Argumenty Funkcji', content='...', order=2)
            lesson3_3 = Lesson(module=mod3, name='Zasięg Zmiennych', content='...', order=3)
            lesson3_4 = Lesson(module=mod3, name='Moduły i Pakiety', content='...', order=4)
            lesson3_5 = Lesson(module=mod3, name='Tworzenie Własnych Modułów', content='...', order=5)
            db.session.add_all([lesson3_1, lesson3_2, lesson3_3, lesson3_4, lesson3_5])


            # Kurs Full Stack Developer
            fullstack_course = Course(
                name='Full Stack Developer',
                description='Kompleksowy kurs tworzenia pełnych aplikacji webowych.',
                gradient_class='course-gradient-fullstack',
                total_lessons=100
            )
            db.session.add(fullstack_course)

            # Moduły do kursu Full Stack (przykładowo)
            fs_mod1 = Module(course=fullstack_course, name='FS Moduł 1: Wprowadzenie do Frontend', total_lessons=10, gradient_class='module-gradient-fullstack-1')
            fs_mod2 = Module(course=fullstack_course, name='FS Moduł 2: Podstawy Backend', total_lessons=15, gradient_class='module-gradient-fullstack-2')
            db.session.add_all([fs_mod1, fs_mod2])

            # Przypisz kursy do użytkownika admina
            user_python_course = UserCourse(user=admin_user, course=python_course, lessons_completed=32) # Ukończony Python
            user_fullstack_course = UserCourse(user=admin_user, course=fullstack_course, lessons_completed=15) # W trakcie Full Stack
            db.session.add_all([user_python_course, user_fullstack_course])

            db.session.commit()
            print("Przykładowe dane dodane.")
        else:
            print("Baza danych już zawiera dane. Jeśli chcesz ją zresetować, usuń plik 'site.db' w folderze 'instance'.")


# === Flask Routes ===

# Strona główna
@app.route('/')
def index():
    if 'user_id' in session:
        # Jeśli użytkownik zalogowany, przekieruj do panelu nauki
        return redirect(url_for('learn'))
    # Jeśli niezalogowany, przekieruj do strony logowania
    return render_template('index.html') # Zmieniono na renderowanie index.html

# Logowanie
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # Jeśli już zalogowany, przekieruj do panelu nauki
        return redirect(url_for('learn'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('learn'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')
    return render_template('login.html')

# Wylogowanie
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Zostałeś wylogowany.', 'info')
    return redirect(url_for('login')) # Po wylogowaniu kieruj na stronę logowania

# Panel nauki (learn.html)
@app.route('/learn')
def learn():
    if 'user_id' not in session:
        flash('Musisz się zalogować, aby uzyskać dostęp do kursów.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    current_user = User.query.get(user_id)

    if not current_user:
        flash('Użytkownik nie znaleziony.', 'error')
        return redirect(url_for('logout'))

    user_courses_data = []
    for uc in current_user.courses:
        course = Course.query.get(uc.course_id)
        if course:
            modules_data = []
            for module in course.modules:
                lessons_in_module = Lesson.query.filter_by(module_id=module.id).count()
                lessons_completed_in_module = 0

                # Przykładowa logika postępu modułu (możesz dostosować)
                # Dla uproszczenia: jeśli kurs jest ukończony, moduły są ukończone.
                # Jeśli w trakcie, ustalamy postęp modułu na podstawie całkowitego postępu kursu,
                # lub specyficznie dla modułów, jak w poprzedniej wersji.
                if uc.lessons_completed >= course.total_lessons:
                    lessons_completed_in_module = lessons_in_module
                elif course.name == 'Python Programming Language' and module.name == 'Moduł 4: Programowanie Obiektowe':
                    lessons_completed_in_module = 2 # Przykład postępu
                elif course.name == 'Full Stack Developer' and module.name == 'FS Moduł 1: Wprowadzenie do Frontend':
                    lessons_completed_in_module = 10
                elif course.name == 'Full Stack Developer' and module.name == 'FS Moduł 2: Podstawy Backend':
                    lessons_completed_in_module = 5


                module_status = "not_started"
                if lessons_completed_in_module == lessons_in_module and lessons_in_module > 0:
                    module_status = "completed"
                elif lessons_completed_in_module > 0 and lessons_completed_in_module < lessons_in_module:
                    module_status = "in_progress"


                modules_data.append({
                    "id": module.id,
                    "title": module.name,
                    "lessons_completed": lessons_completed_in_module,
                    "total_lessons": lessons_in_module,
                    "status": module_status,
                    "gradient_class": module.gradient_class
                })

            course_progress_percent = 0
            if course.total_lessons > 0:
                course_progress_percent = (uc.lessons_completed / course.total_lessons) * 100

            user_courses_data.append({
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "gradient_class": course.gradient_class,
                "progress_lessons_completed": uc.lessons_completed,
                "progress_total_lessons": course.total_lessons,
                "progress_percent": int(course_progress_percent),
                "modules": modules_data,
                "tabs": ["Na lekcji", "Zadanie domowe", "Ocena"]
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

    return render_template(
        'learn.html',
        user_courses=user_courses_data,
        active_course=active_course,
        username=current_user.username,
        lessons_balance=current_user.lessons_balance
    )

# Pozostałe trasy
@app.route("/hire.html")
def hire():
    return render_template("hire.html")

@app.route("/projects.html")
def projects():
    return render_template("projects.html")

@app.route("/plan.html")
def plan():
    return render_template("plan.html")

@app.route("/python.html")
def view():
    return render_template("python.html")

@app.route("/full.html")
def full():
    return render_template("full.html")

@app.route("/frontend.html")
def frontend():
    return render_template("frontend.html")

@app.route("/backend.html")
def backend():
    return render_template("backend.html")

@app.route("/AI.html")
def ai():
    return render_template("AI.html")


if __name__ == '__main__':
    with app.app_context():
        init_db_and_data()
    app.run(debug=True)
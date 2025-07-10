from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
bcrypt = Bcrypt(app)
# Konfiguracja bazy danych SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

db = SQLAlchemy(app)

# Utwórz folder 'instance' jeśli nie istnieje
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# === UPROSZCZONA FUNKCJA HASZOWANIA I SPRAWDZANIA HASŁA BEZ WERKZEUG (NIEBEZPIECZNE W PRODUKCJI) ===
# TA IMPLEMENTACJA JEST TYLKO DO CELÓW DEMONSTRACYJNYCH.
# W PRAWDZIWEJ APLIKACJI UŻYWAJ SPRAWDZONYCH BIBLIOTEK KRYPTOGRAFICZNYCH (np. Flask-Bcrypt, Werkzeug.security).
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16) # Generuj losową sól (16 bajtów)
    salted_password = salt + password.encode('utf-8')
    return salt + hashlib.sha256(salted_password).digest()

def check_password(hashed_password_with_salt, password):
    salt = hashed_password_with_salt[:16]
    stored_hash = hashed_password_with_salt[16:]
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
        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    gradient_class = db.Column(db.String(50), nullable=False) # Klasa CSS dla gradientu
    total_lessons = db.Column(db.Integer, default=0) # Całkowita liczba lekcji w kursie (zaktualizowana w init_db)
    modules = db.relationship('Module', backref='course', lazy=True)

    def __repr__(self):
        return f'<Course {self.name}>'

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    total_lessons = db.Column(db.Integer, default=0) # Całkowita liczba lekcji w module (zaktualizowana w init_db)
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
        # lub po prostu chcesz zresetować bazę danych, MUSISZ USUNĄĆ plik 'site.db'
        # z folderu 'instance' przed ponownym uruchomieniem.
        db.create_all() # Tworzy wszystkie tabele

        # Dodaj przykładowe dane, jeśli baza jest pusta
        if not User.query.first():
            print("Dodawanie przykładowych danych...")

            # Użytkownik Admin - TYLKO DLA CIEBIE
            # ZMIEN TO NA SWÓJ E-MAIL I HASŁO!
            admin_email = "grzegorzgladysz2204@gmail.com"
            admin_password = "Lego2012"

            admin_user = User(username='admin', email=admin_email, lessons_balance=100)
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit() # Zatwierdź użytkownika, aby otrzymał ID

            # Kurs Python Programming Language
            python_course = Course(
                name='Python Programming Language',
                description='Kompleksowy kurs programowania w Pythonie od podstaw.',
                gradient_class='course-gradient-python',
                total_lessons=32 # Suma lekcji ze wszystkich modułów Pythona
            )
            db.session.add(python_course)
            db.session.commit() # Zatwierdź kurs, aby otrzymał ID

            # Moduły do kursu Python - Upewnij się, że total_lessons > 0 dla KAŻDEGO MODUŁU
            mod1 = Module(course_id=python_course.id, name='Moduł 1: Podstawy Pythona', total_lessons=4, gradient_class='module-gradient-1')
            mod2 = Module(course_id=python_course.id, name='Moduł 2: Struktury Danych', total_lessons=4, gradient_class='module-gradient-2')
            mod3 = Module(course_id=python_course.id, name='Moduł 3: Funkcje i Moduły', total_lessons=5, gradient_class='module-gradient-3')
            mod4 = Module(course_id=python_course.id, name='Moduł 4: Programowanie Obiektowe', total_lessons=5, gradient_class='module-gradient-4')
            mod5 = Module(course_id=python_course.id, name='Moduł 5: Obsługa Plików i Wyjątków', total_lessons=6, gradient_class='module-gradient-5')
            db.session.add_all([mod1, mod2, mod3, mod4, mod5])
            db.session.commit() # Zatwierdź moduły, aby otrzymały ID

            # Lekcje do Modułu 1 (Python)
            lesson1_1 = Lesson(module_id=mod1.id, name='Wprowadzenie do Pythona', content='...', order=1)
            lesson1_2 = Lesson(module_id=mod1.id, name='Zmienne i Typy Danych', content='...', order=2)
            lesson1_3 = Lesson(module_id=mod1.id, name='Operatory', content='...', order=3)
            lesson1_4 = Lesson(module_id=mod1.id, name='Instrukcje Warunkowe', content='...', order=4)
            db.session.add_all([lesson1_1, lesson1_2, lesson1_3, lesson1_4])
            db.session.commit() # Zatwierdź lekcje

            # Lekcje do Modułu 2 (Python)
            lesson2_1 = Lesson(module_id=mod2.id, name='Listy', content='...', order=1)
            lesson2_2 = Lesson(module_id=mod2.id, name='Krotki', content='...', order=2)
            lesson2_3 = Lesson(module_id=mod2.id, name='Zbiory', content='...', order=3)
            lesson2_4 = Lesson(module_id=mod2.id, name='Słowniki', content='...', order=4)
            db.session.add_all([lesson2_1, lesson2_2, lesson2_3, lesson2_4])
            db.session.commit()

            # Lekcje do Modułu 3 (Python)
            lesson3_1 = Lesson(module_id=mod3.id, name='Definiowanie Funkcji', content='...', order=1)
            lesson3_2 = Lesson(module_id=mod3.id, name='Argumenty Funkcji', content='...', order=2)
            lesson3_3 = Lesson(module_id=mod3.id, name='Zasięg Zmiennych', content='...', order=3)
            lesson3_4 = Lesson(module_id=mod3.id, name='Moduły i Pakiety', content='...', order=4)
            lesson3_5 = Lesson(module_id=mod3.id, name='Tworzenie Własnych Modułów', content='...', order=5)
            db.session.add_all([lesson3_1, lesson3_2, lesson3_3, lesson3_4, lesson3_5])
            db.session.commit()

            # ... Dodaj lekcje do Modułu 4 i Modułu 5, upewniając się, że masz dokładnie 5 lekcji w M4 i 6 w M5
            # Poniżej są tylko przykłady, musisz uzupełnić content
            lesson4_1 = Lesson(module_id=mod4.id, name='Klasy i Obiekty', content='...', order=1)
            lesson4_2 = Lesson(module_id=mod4.id, name='Dziedziczenie', content='...', order=2)
            lesson4_3 = Lesson(module_id=mod4.id, name='Polimorfizm', content='...', order=3)
            lesson4_4 = Lesson(module_id=mod4.id, name='Hermetyzacja', content='...', order=4)
            lesson4_5 = Lesson(module_id=mod4.id, name='Metody Specjalne', content='...', order=5)
            db.session.add_all([lesson4_1, lesson4_2, lesson4_3, lesson4_4, lesson4_5])
            db.session.commit()

            lesson5_1 = Lesson(module_id=mod5.id, name='Odczyt Plików', content='...', order=1)
            lesson5_2 = Lesson(module_id=mod5.id, name='Zapis do Plików', content='...', order=2)
            lesson5_3 = Lesson(module_id=mod5.id, name='Zarządzanie Ścieżkami', content='...', order=3)
            lesson5_4 = Lesson(module_id=mod5.id, name='Obsługa Wyjątków Try-Except', content='...', order=4)
            lesson5_5 = Lesson(module_id=mod5.id, name='Tworzenie Własnych Wyjątków', content='...', order=5)
            lesson5_6 = Lesson(module_id=mod5.id, name='Debugowanie', content='...', order=6)
            db.session.add_all([lesson5_1, lesson5_2, lesson5_3, lesson5_4, lesson5_5, lesson5_6])
            db.session.commit()
            # Koniec dodawania lekcji do modułów 4 i 5

            # Kurs Full Stack Developer
            fullstack_course = Course(
                name='Full Stack Developer',
                description='Kompleksowy kurs tworzenia pełnych aplikacji webowych.',
                gradient_class='course-gradient-fullstack',
                total_lessons=100 # Przykładowa liczba, dostosuj do rzeczywistej liczby lekcji
            )
            db.session.add(fullstack_course)
            db.session.commit() # Zatwierdź kurs, aby otrzymał ID

            # Moduły do kursu Full Stack (przykładowo) - Upewnij się, że total_lessons > 0
            fs_mod1 = Module(course_id=fullstack_course.id, name='FS Moduł 1: Wprowadzenie do Frontend', total_lessons=10, gradient_class='module-gradient-fullstack-1')
            fs_mod2 = Module(course_id=fullstack_course.id, name='FS Moduł 2: Podstawy Backend', total_lessons=15, gradient_class='module-gradient-fullstack-2')
            # Pamiętaj, aby dodać lekcje do tych modułów!
            db.session.add_all([fs_mod1, fs_mod2])
            db.session.commit()

            # Przypisz kursy do użytkownika admina
            # Zmienilem lessons_completed dla Pythona na 0, zeby pokazac postep od nowa
            user_python_course = UserCourse(user_id=admin_user.id, course_id=python_course.id, lessons_completed=0) # Teraz admin ma 0 ukończonych lekcji Pythona
            user_fullstack_course = UserCourse(user_id=admin_user.id, course_id=fullstack_course.id, lessons_completed=15) # W trakcie Full Stack
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
    # Jeśli niezalogowany, przekieruj do strony głównej (index.html)
    return render_template('index.html')


# Logowanie
# Zmieniono ścieżkę z '/login.html' na '/login' dla spójności
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
# Zmieniono ścieżkę z '/learn.html' na '/learn' dla spójności
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

                # Logika postępu modułu:
                # Jeśli kurs jest w pełni ukończony przez użytkownika,
                # to wszystkie moduły w tym kursie również są uznawane za ukończone.
                if uc.lessons_completed >= course.total_lessons and course.total_lessons > 0:
                    lessons_completed_in_module = lessons_in_module
                # W przeciwnym razie, użyj specyficznej logiki postępu dla poszczególnych modułów
                # Pamiętaj, aby lessons_completed_in_module nie przekraczało lessons_in_module!
                elif course.name == 'Python Programming Language':
                    if module.name == 'Moduł 1: Podstawy Pythona':
                        lessons_completed_in_module = min(4, uc.lessons_completed) # Przykładowo, jeśli user ukończył 4 lekcje, ten moduł jest pełny
                    elif module.name == 'Moduł 2: Struktury Danych':
                        lessons_completed_in_module = min(4, max(0, uc.lessons_completed - 4)) # Przykładowo, liczy od lekcji 5 do 8
                    elif module.name == 'Moduł 3: Funkcje i Moduły':
                         lessons_completed_in_module = min(5, max(0, uc.lessons_completed - 8)) # Liczy od lekcji 9 do 13
                    elif module.name == 'Moduł 4: Programowanie Obiektowe':
                         lessons_completed_in_module = min(5, max(0, uc.lessons_completed - 13)) # Liczy od lekcji 14 do 18
                    elif module.name == 'Moduł 5: Obsługa Plików i Wyjątków':
                         lessons_completed_in_module = min(6, max(0, uc.lessons_completed - 18)) # Liczy od lekcji 19 do 24
                elif course.name == 'Full Stack Developer':
                    if module.name == 'FS Moduł 1: Wprowadzenie do Frontend':
                        lessons_completed_in_module = 10
                    elif module.name == 'FS Moduł 2: Podstawy Backend':
                        lessons_completed_in_module = 5
                # Domyślnie, jeśli nie ma specyficznej logiki i nie jest ukończony kurs, to 0.

                module_status = "not_started"
                # Upewnij się, że lessons_in_module jest większe od 0 przed dzieleniem
                if lessons_in_module > 0 and lessons_completed_in_module == lessons_in_module:
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
            # Zabezpieczenie przed ZeroDivisionError w Pythonie
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
        active_course = user_courses_data[0] # Ustawia pierwszy kurs jako aktywny domyślnie

    return render_template(
        'learn.html',
        user_courses=user_courses_data,
        active_course=active_course,
        username=current_user.username,
        lessons_balance=current_user.lessons_balance
    )

# Pozostałe trasy (bez zmian w stosunku do poprzedniej wersji, zgodne z Twoim repozytorium)
@app.route("/hire")
def hire():
    return render_template("hire.html")

@app.route("/projects")
def projects():
    return render_template("projects.html")

@app.route("/plan")
def plan():
    return render_template("plan.html")

@app.route("/python") # Bylo view, ale zmienilem na python dla spójności
def python(): # To jest funkcja, która odpowiada za trasę "/python" (python.html)
    return render_template("python.html")

@app.route("/full")
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


if __name__ == '__main__':
    with app.app_context():
        init_db_and_data()
    app.run(debug=True)
# your_project/models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) # Zwiększono rozmiar dla bezpieczeństwa hashy
    role = db.Column(db.String(20), default='user', nullable=False) # 'user', 'admin'. Dodano nullable=False
    lessons_balance = db.Column(db.Integer, default=0, nullable=False) # Dodano nullable=False
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacje - jeden użytkownik może mieć wiele UserCourseAccess
    course_accesses = db.relationship('UserCourseAccess', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'

    # Dodane metody do zarządzania hasłem (używane w main.py)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    gradient_class = db.Column(db.String(50), default='course-gradient-default')
    total_lessons = db.Column(db.Integer, default=0, nullable=False) # <--- WAŻNE: TA LINIA JEST DODANA!
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacja do modułów (jeden kurs ma wiele modułów)
    modules = db.relationship('Module', backref='course', lazy=True, cascade="all, delete-orphan", order_by="Module.order")
    # Relacja do UserCourseAccess (kursy przypisane użytkownikom)
    user_accesses = db.relationship('UserCourseAccess', backref='course', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Course {self.name}>'

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Zmieniono 'title' na 'name', aby zachować spójność z innymi modelami i logiką w main.py
    name = db.Column(db.String(150), nullable=False)
    order = db.Column(db.Integer, nullable=False) # Kolejność modułów w kursie
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    gradient_class = db.Column(db.String(50), default='module-gradient-default')
    total_lessons = db.Column(db.Integer, default=0, nullable=False) # <--- WAŻNE: TA LINIA JEST DODANA!
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacje - jeden moduł ma wiele lekcji
    lessons = db.relationship('Lesson', backref='module', lazy=True, cascade="all, delete-orphan", order_by="Lesson.order")

    def __repr__(self):
        return f'<Module {self.name}>'

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False) # Kolejność lekcji w module
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Lesson {self.name}>'

# Tabela pośrednicząca do zarządzania dostępem użytkowników do kursów i postępów
class UserCourseAccess(db.Model):
    __tablename__ = 'user_course_access' # Nazwa tabeli
    id = db.Column(db.Integer, primary_key=True) # Dodano ID jako Primary Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    lessons_completed = db.Column(db.Integer, default=0, nullable=False) # <--- WAŻNE: TA LINIA JEST DODANA!
    current_lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=True) # <--- WAŻNE: TA LINIA JEST DODANA!
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Opcjonalnie, możesz dodać ograniczenie unikalności, jeśli user_id i course_id mają być zawsze unikalne razem
    # db.UniqueConstraint('user_id', 'course_id', name='_user_course_uc')

    def __repr__(self):
        return f'<UserCourseAccess UserID: {self.user_id}, CourseID: {self.course_id}>'

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # A2F TOTP
    totp_secret = db.Column(db.String(32), nullable=True)
    totp_enabled = db.Column(db.Boolean, default=False, nullable=False)

    sessions = db.relationship('QcmSession', backref='user', lazy=True, cascade='all, delete-orphan')
    cheat_logs = db.relationship('CheatLog', backref='user', lazy=True, cascade='all, delete-orphan')

    @property
    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default='normal', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    options = db.relationship('Option', backref='question', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('UserAnswer', backref='question', lazy=True)

    def get_correct_option(self):
        return next((o for o in self.options if o.is_correct), None)

    def __repr__(self):
        return f'<Question {self.id}: {self.text[:40]}>'


class Option(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Option {self.id}: {self.text[:30]}>'


class ScheduledQuiz(db.Model):
    __tablename__ = 'scheduled_quizzes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    question_count = db.Column(db.Integer, default=10)
    category_filter = db.Column(db.String(50))   # None = toutes catégories
    difficulty_filter = db.Column(db.String(20)) # None = toutes difficultés
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship('QcmSession', backref='scheduled_quiz', lazy=True)

    @property
    def is_available_now(self):
        now = datetime.utcnow()
        return self.is_active and self.start_time <= now <= self.end_time

    @property
    def status(self):
        now = datetime.utcnow()
        if not self.is_active:
            return 'inactive'
        if now < self.start_time:
            return 'upcoming'
        if now > self.end_time:
            return 'expired'
        return 'active'

    def __repr__(self):
        return f'<ScheduledQuiz {self.name}>'


class QcmSession(db.Model):
    __tablename__ = 'qcm_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scheduled_quiz_id = db.Column(db.Integer, db.ForeignKey('scheduled_quizzes.id'), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float, default=0.0)
    total_questions = db.Column(db.Integer, default=10)
    cheat_count = db.Column(db.Integer, default=0)
    time_exceeded = db.Column(db.Boolean, default=False)

    answers = db.relationship('UserAnswer', backref='session', lazy=True, cascade='all, delete-orphan')
    cheat_logs = db.relationship('CheatLog', backref='session', lazy=True, cascade='all, delete-orphan')
    session_questions = db.relationship('QcmSessionQuestion', backref='session', lazy=True,
                                        cascade='all, delete-orphan', order_by='QcmSessionQuestion.order')

    @property
    def score_on_20(self):
        return round(self.score, 2)

    @property
    def duration_seconds(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def __repr__(self):
        return f'<QcmSession {self.id} user={self.user_id}>'


class QcmSessionQuestion(db.Model):
    __tablename__ = 'qcm_session_questions'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('qcm_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)

    question = db.relationship('Question')


class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('qcm_sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    chosen_option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=True)
    is_correct = db.Column(db.Boolean, default=False)

    chosen_option = db.relationship('Option')


class CheatLog(db.Model):
    __tablename__ = 'cheat_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('qcm_sessions.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

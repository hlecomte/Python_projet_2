from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (StringField, PasswordField, SelectField, TextAreaField,
                     BooleanField, EmailField, IntegerField, DateTimeField)
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange


class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(message="Champ requis")])
    password = PasswordField('Mot de passe', validators=[DataRequired(message="Champ requis")])


class TotpForm(FlaskForm):
    code = StringField('Code à 6 chiffres', validators=[
        DataRequired(message="Champ requis"),
        Length(min=6, max=6, message="Le code doit contenir exactement 6 chiffres")
    ])


class RegisterForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[
        DataRequired(message="Champ requis"),
        Length(min=3, max=80, message="Entre 3 et 80 caractères")
    ])
    email = EmailField('Adresse e-mail', validators=[
        DataRequired(message="Champ requis"),
        Email(message="Adresse e-mail invalide")
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message="Champ requis"),
        Length(min=8, message="Minimum 8 caractères")
    ])
    confirm = PasswordField('Confirmer le mot de passe', validators=[
        DataRequired(message="Champ requis"),
        EqualTo('password', message="Les mots de passe ne correspondent pas")
    ])

    def validate_username(self, field):
        from models import User
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Ce nom d'utilisateur est déjà pris.")

    def validate_email(self, field):
        from models import User
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Cette adresse e-mail est déjà utilisée.")


class QuestionForm(FlaskForm):
    text = TextAreaField('Énoncé de la question', validators=[
        DataRequired(message="Champ requis"),
        Length(min=5, max=1000)
    ])
    category = SelectField('Catégorie', choices=[
        ('Réseaux', 'Réseaux'),
        ('Sécurité', 'Sécurité'),
        ('Système', 'Système'),
        ('Programmation', 'Programmation'),
        ('Base de données', 'Base de données'),
    ])
    difficulty = SelectField('Difficulté', choices=[
        ('facile', 'Facile'),
        ('normal', 'Normal'),
        ('difficile', 'Difficile'),
    ])
    option_a = StringField('Option A', validators=[DataRequired(message="Champ requis"), Length(max=500)])
    option_b = StringField('Option B', validators=[DataRequired(message="Champ requis"), Length(max=500)])
    option_c = StringField('Option C', validators=[DataRequired(message="Champ requis"), Length(max=500)])
    option_d = StringField('Option D', validators=[DataRequired(message="Champ requis"), Length(max=500)])
    correct = SelectField('Bonne réponse', choices=[
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')
    ])


class CsvImportForm(FlaskForm):
    csv_file = FileField('Fichier CSV', validators=[
        FileRequired(message="Sélectionnez un fichier CSV"),
        FileAllowed(['csv'], 'Fichier CSV uniquement (.csv)')
    ])


class UserAdminForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[
        DataRequired(message="Champ requis"),
        Length(min=3, max=80)
    ])
    email = EmailField('Adresse e-mail', validators=[
        DataRequired(message="Champ requis"),
        Email(message="Adresse e-mail invalide")
    ])
    password = PasswordField('Mot de passe (laisser vide pour ne pas changer)', validators=[
        Optional(),
        Length(min=8, message="Minimum 8 caractères")
    ])
    role = SelectField('Rôle', choices=[
        ('student', 'Étudiant'),
        ('admin', 'Administrateur')
    ])
    is_active = BooleanField('Compte actif', default=True)


class ScheduledQuizForm(FlaskForm):
    name = StringField('Nom du quiz', validators=[
        DataRequired(message="Champ requis"),
        Length(max=100)
    ])
    description = TextAreaField('Description (optionnel)', validators=[Optional()])
    start_time = DateTimeField('Date/heure de début', validators=[DataRequired()],
                               format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('Date/heure de fin', validators=[DataRequired()],
                             format='%Y-%m-%dT%H:%M')
    question_count = IntegerField('Nombre de questions', validators=[
        DataRequired(), NumberRange(min=1, max=50)
    ], default=10)
    category_filter = SelectField('Catégorie (optionnel)', choices=[
        ('', 'Toutes les catégories'),
        ('Réseaux', 'Réseaux'),
        ('Sécurité', 'Sécurité'),
        ('Système', 'Système'),
        ('Programmation', 'Programmation'),
        ('Base de données', 'Base de données'),
    ], validators=[Optional()])
    difficulty_filter = SelectField('Difficulté (optionnel)', choices=[
        ('', 'Toutes difficultés'),
        ('facile', 'Facile'),
        ('normal', 'Normal'),
        ('difficile', 'Difficile'),
    ], validators=[Optional()])
    is_active = BooleanField('Actif', default=True)

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("La fin doit être après le début.")

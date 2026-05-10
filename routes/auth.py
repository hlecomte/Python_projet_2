import pyotp
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User
from forms import LoginForm, RegisterForm, TotpForm

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard') if not current_user.is_admin else url_for('admin.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.is_active and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if user.totp_enabled:
                session['pending_2fa_user_id'] = user.id
                return redirect(url_for('auth.login_2fa'))
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or (url_for('admin.dashboard') if user.is_admin else url_for('student.dashboard')))
        flash("Nom d'utilisateur ou mot de passe incorrect.", 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/login/2fa', methods=['GET', 'POST'])
def login_2fa():
    user_id = session.get('pending_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user or not user.totp_enabled:
        session.pop('pending_2fa_user_id', None)
        return redirect(url_for('auth.login'))

    form = TotpForm()
    if form.validate_on_submit():
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(form.code.data.strip(), valid_window=1):
            session.pop('pending_2fa_user_id', None)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or (url_for('admin.dashboard') if user.is_admin else url_for('student.dashboard')))
        flash('Code incorrect. Réessayez.', 'danger')

    return render_template('auth/verify_2fa.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        totp_secret = pyotp.random_base32()
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            password_hash=hashed,
            role='student',
            totp_secret=totp_secret,
            totp_enabled=False
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Compte créé ! Configurez maintenant votre authentification à deux facteurs (A2F).", 'info')
        return redirect(url_for('auth.setup_2fa'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/setup-2fa')
@login_required
def setup_2fa():
    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        db.session.commit()

    totp = pyotp.TOTP(current_user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name='QCM Sécurisé'
    )
    return render_template('auth/setup_2fa.html',
                           provisioning_uri=provisioning_uri,
                           secret=current_user.totp_secret,
                           form=TotpForm())


@auth_bp.route('/setup-2fa/confirm', methods=['POST'])
@login_required
def confirm_2fa():
    form = TotpForm()
    if form.validate_on_submit():
        if not current_user.totp_secret:
            flash('Erreur de configuration A2F.', 'danger')
            return redirect(url_for('auth.setup_2fa'))

        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(form.code.data.strip(), valid_window=1):
            current_user.totp_enabled = True
            db.session.commit()
            flash('Authentification à deux facteurs (A2F) activée avec succès !', 'success')
            return redirect(url_for('admin.dashboard') if current_user.is_admin else url_for('student.dashboard'))
        flash('Code incorrect. Vérifiez votre application et réessayez.', 'danger')

    return redirect(url_for('auth.setup_2fa'))


@auth_bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    current_user.totp_enabled = False
    current_user.totp_secret = pyotp.random_base32()
    db.session.commit()
    flash("A2F désactivée.", 'warning')
    return redirect(url_for('student.dashboard') if not current_user.is_admin else url_for('admin.dashboard'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté.", 'info')
    return redirect(url_for('auth.login'))

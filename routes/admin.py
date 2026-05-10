import csv
import io
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, abort, Response)
from flask_login import login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Question, Option, QcmSession, UserAnswer, CheatLog, ScheduledQuiz
from forms import QuestionForm, UserAdminForm, ScheduledQuizForm, CsvImportForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
bcrypt = Bcrypt()


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.filter_by(role='student').count()
    total_questions = Question.query.count()
    active_questions = Question.query.filter_by(is_active=True).count()
    total_attempts = QcmSession.query.filter_by(is_completed=True).count()

    avg_score = 0
    if total_attempts > 0:
        scores = [s.score for s in QcmSession.query.filter_by(is_completed=True).all()]
        avg_score = round(sum(scores) / len(scores), 2)

    recent_sessions = (QcmSession.query
                       .filter_by(is_completed=True)
                       .order_by(QcmSession.end_time.desc())
                       .limit(10).all())

    from sqlalchemy import func
    missed = (db.session.query(Question, func.count(UserAnswer.id).label('miss_count'))
              .join(UserAnswer, UserAnswer.question_id == Question.id)
              .filter(UserAnswer.is_correct == False)
              .group_by(Question.id)
              .order_by(func.count(UserAnswer.id).desc())
              .limit(5).all())

    score_distribution = {str(i * 2): 0 for i in range(11)}
    for s in QcmSession.query.filter_by(is_completed=True).all():
        key = str(int(s.score))
        if key in score_distribution:
            score_distribution[key] += 1

    upcoming_quizzes = (ScheduledQuiz.query
                        .filter_by(is_active=True)
                        .filter(ScheduledQuiz.end_time >= datetime.utcnow())
                        .order_by(ScheduledQuiz.start_time)
                        .limit(3).all())

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_questions=total_questions,
                           active_questions=active_questions,
                           total_attempts=total_attempts,
                           avg_score=avg_score,
                           recent_sessions=recent_sessions,
                           missed_questions=missed,
                           score_distribution=score_distribution,
                           upcoming_quizzes=upcoming_quizzes)


# ─── USERS ───────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )
    users_list = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users_list, search=search)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    form = UserAdminForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Ce nom d'utilisateur est déjà pris.", 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash("Cette adresse e-mail est déjà utilisée.", 'danger')
        elif not form.password.data:
            flash("Le mot de passe est requis pour la création.", 'danger')
        else:
            import pyotp
            hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(
                username=form.username.data.strip(),
                email=form.email.data.strip().lower(),
                password_hash=hashed,
                role=form.role.data,
                is_active=form.is_active.data,
                totp_secret=pyotp.random_base32(),
                totp_enabled=False
            )
            db.session.add(user)
            db.session.commit()
            flash(f"Utilisateur '{user.username}' créé. L'A2F sera configurée à sa première connexion.", 'success')
            return redirect(url_for('admin.users'))
    return render_template('admin/users_form.html', form=form, title='Nouvel utilisateur', is_edit=False)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserAdminForm(obj=user)

    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing and existing.id != user.id:
            flash("Ce nom d'utilisateur est déjà pris.", 'danger')
        else:
            user.username = form.username.data.strip()
            user.email = form.email.data.strip().lower()
            user.role = form.role.data
            user.is_active = form.is_active.data
            if form.password.data:
                user.password_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            db.session.commit()
            flash(f"Utilisateur '{user.username}' mis à jour.", 'success')
            return redirect(url_for('admin.users'))

    return render_template('admin/users_form.html', form=form,
                           title="Modifier l'utilisateur", user=user, is_edit=True)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Vous ne pouvez pas supprimer votre propre compte.", 'danger')
        return redirect(url_for('admin.users'))
    db.session.delete(user)
    db.session.commit()
    flash(f"Utilisateur '{user.username}' supprimé.", 'success')
    return redirect(url_for('admin.users'))


# ─── QUESTIONS ───────────────────────────────────────────────────────────────

@admin_bp.route('/questions')
@login_required
@admin_required
def questions():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    difficulty = request.args.get('difficulty', '')
    search = request.args.get('search', '')
    active_filter = request.args.get('active', '')

    query = Question.query
    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if active_filter == '1':
        query = query.filter_by(is_active=True)
    elif active_filter == '0':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(Question.text.ilike(f'%{search}%'))

    questions_list = query.order_by(Question.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    categories = [c[0] for c in db.session.query(Question.category).distinct().all()]

    return render_template('admin/questions.html',
                           questions=questions_list,
                           categories=categories,
                           selected_category=category,
                           selected_difficulty=difficulty,
                           selected_active=active_filter,
                           search=search)


@admin_bp.route('/questions/<int:question_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_question(question_id):
    q = Question.query.get_or_404(question_id)
    q.is_active = not q.is_active
    db.session.commit()
    state = "activée" if q.is_active else "désactivée"
    flash(f"Question #{q.id} {state}.", 'success')
    return redirect(request.referrer or url_for('admin.questions'))


@admin_bp.route('/questions/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_question():
    form = QuestionForm()
    if form.validate_on_submit():
        q = Question(text=form.text.data.strip(), category=form.category.data,
                     difficulty=form.difficulty.data)
        db.session.add(q)
        db.session.flush()
        _save_options(q.id, form)
        db.session.commit()
        flash("Question ajoutée.", 'success')
        return redirect(url_for('admin.questions'))
    return render_template('admin/questions_form.html', form=form, title='Nouvelle question', is_edit=False)


@admin_bp.route('/questions/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(question_id):
    q = Question.query.get_or_404(question_id)
    opts = sorted(q.options, key=lambda o: o.order)
    letter_map = ['a', 'b', 'c', 'd']
    correct_letter = next((letter_map[i] for i, o in enumerate(opts) if o.is_correct), 'a')

    form = QuestionForm(data={
        'text': q.text, 'category': q.category, 'difficulty': q.difficulty,
        'option_a': opts[0].text if len(opts) > 0 else '',
        'option_b': opts[1].text if len(opts) > 1 else '',
        'option_c': opts[2].text if len(opts) > 2 else '',
        'option_d': opts[3].text if len(opts) > 3 else '',
        'correct': correct_letter,
    })

    if form.validate_on_submit():
        q.text = form.text.data.strip()
        q.category = form.category.data
        q.difficulty = form.difficulty.data
        options_texts = [form.option_a.data, form.option_b.data,
                         form.option_c.data, form.option_d.data]
        for i, opt in enumerate(opts):
            opt.text = options_texts[i].strip()
            opt.is_correct = (letter_map[i] == form.correct.data)
        db.session.commit()
        flash("Question mise à jour.", 'success')
        return redirect(url_for('admin.questions'))

    return render_template('admin/questions_form.html', form=form,
                           title='Modifier la question', question=q, is_edit=True)


@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    q = Question.query.get_or_404(question_id)
    db.session.delete(q)
    db.session.commit()
    flash("Question supprimée.", 'success')
    return redirect(url_for('admin.questions'))


@admin_bp.route('/questions/import', methods=['GET', 'POST'])
@login_required
@admin_required
def import_questions():
    form = CsvImportForm()
    results = None

    if form.validate_on_submit():
        file = form.csv_file.data
        try:
            content = file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(content))
            added, errors = 0, []
            letter_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}

            for row_num, row in enumerate(reader, start=2):
                try:
                    text = row.get('question', '').strip()
                    category = row.get('category', '').strip()
                    difficulty = row.get('difficulty', 'normal').strip()
                    opt_a = row.get('option_a', '').strip()
                    opt_b = row.get('option_b', '').strip()
                    opt_c = row.get('option_c', '').strip()
                    opt_d = row.get('option_d', '').strip()
                    correct = row.get('correct', '').strip().lower()

                    if not all([text, category, opt_a, opt_b, opt_c, opt_d, correct]):
                        errors.append(f"Ligne {row_num}: colonnes manquantes")
                        continue
                    if correct not in letter_map:
                        errors.append(f"Ligne {row_num}: 'correct' doit être a, b, c ou d")
                        continue
                    if category not in ['Réseaux', 'Sécurité', 'Système', 'Programmation', 'Base de données']:
                        errors.append(f"Ligne {row_num}: catégorie inconnue '{category}'")
                        continue

                    q = Question(text=text, category=category, difficulty=difficulty)
                    db.session.add(q)
                    db.session.flush()

                    correct_idx = letter_map[correct]
                    for i, opt_text in enumerate([opt_a, opt_b, opt_c, opt_d]):
                        db.session.add(Option(
                            question_id=q.id, text=opt_text,
                            is_correct=(i == correct_idx), order=i
                        ))
                    added += 1
                except Exception as e:
                    errors.append(f"Ligne {row_num}: {e}")

            db.session.commit()
            results = {'added': added, 'errors': errors}
            if added:
                flash(f"{added} question(s) importée(s) avec succès.", 'success')
        except Exception as e:
            flash(f"Erreur de lecture du fichier : {e}", 'danger')

    return render_template('admin/import_questions.html', form=form, results=results)


def _save_options(question_id, form):
    letter_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
    correct_idx = letter_map[form.correct.data]
    options_texts = [form.option_a.data, form.option_b.data,
                     form.option_c.data, form.option_d.data]
    for i, text in enumerate(options_texts):
        db.session.add(Option(
            question_id=question_id, text=text.strip(),
            is_correct=(i == correct_idx), order=i
        ))


# ─── QUIZ PLANIFIÉS ──────────────────────────────────────────────────────────

@admin_bp.route('/quizzes')
@login_required
@admin_required
def quizzes():
    now = datetime.utcnow()
    all_quizzes = ScheduledQuiz.query.order_by(ScheduledQuiz.start_time.desc()).all()
    return render_template('admin/quizzes.html', quizzes=all_quizzes, now=now)


@admin_bp.route('/quizzes/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_quiz():
    form = ScheduledQuizForm()
    if form.validate_on_submit():
        quiz = ScheduledQuiz(
            name=form.name.data.strip(),
            description=form.description.data or '',
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            question_count=form.question_count.data,
            category_filter=form.category_filter.data or None,
            difficulty_filter=form.difficulty_filter.data or None,
            is_active=form.is_active.data
        )
        db.session.add(quiz)
        db.session.commit()
        flash(f"Quiz '{quiz.name}' planifié.", 'success')
        return redirect(url_for('admin.quizzes'))
    return render_template('admin/quizzes_form.html', form=form, title='Nouveau quiz', is_edit=False)


@admin_bp.route('/quizzes/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_quiz(quiz_id):
    quiz = ScheduledQuiz.query.get_or_404(quiz_id)
    form = ScheduledQuizForm(data={
        'name': quiz.name,
        'description': quiz.description,
        'start_time': quiz.start_time,
        'end_time': quiz.end_time,
        'question_count': quiz.question_count,
        'category_filter': quiz.category_filter or '',
        'difficulty_filter': quiz.difficulty_filter or '',
        'is_active': quiz.is_active,
    })

    if form.validate_on_submit():
        quiz.name = form.name.data.strip()
        quiz.description = form.description.data or ''
        quiz.start_time = form.start_time.data
        quiz.end_time = form.end_time.data
        quiz.question_count = form.question_count.data
        quiz.category_filter = form.category_filter.data or None
        quiz.difficulty_filter = form.difficulty_filter.data or None
        quiz.is_active = form.is_active.data
        db.session.commit()
        flash(f"Quiz '{quiz.name}' mis à jour.", 'success')
        return redirect(url_for('admin.quizzes'))

    return render_template('admin/quizzes_form.html', form=form,
                           title='Modifier le quiz', quiz=quiz, is_edit=True)


@admin_bp.route('/quizzes/<int:quiz_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_quiz(quiz_id):
    quiz = ScheduledQuiz.query.get_or_404(quiz_id)
    quiz.is_active = not quiz.is_active
    db.session.commit()
    state = "activé" if quiz.is_active else "désactivé"
    flash(f"Quiz '{quiz.name}' {state}.", 'success')
    return redirect(url_for('admin.quizzes'))


@admin_bp.route('/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_quiz(quiz_id):
    quiz = ScheduledQuiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash(f"Quiz '{quiz.name}' supprimé.", 'success')
    return redirect(url_for('admin.quizzes'))


# ─── STATS & EXPORT ──────────────────────────────────────────────────────────

@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    from sqlalchemy import func
    sessions = QcmSession.query.filter_by(is_completed=True).all()
    scores = [s.score for s in sessions]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    missed = (db.session.query(Question, func.count(UserAnswer.id).label('miss_count'))
              .join(UserAnswer, UserAnswer.question_id == Question.id)
              .filter(UserAnswer.is_correct == False)
              .group_by(Question.id)
              .order_by(func.count(UserAnswer.id).desc())
              .limit(10).all())

    cheat_events = (db.session.query(CheatLog.event_type, func.count(CheatLog.id).label('cnt'))
                    .group_by(CheatLog.event_type)
                    .order_by(func.count(CheatLog.id).desc()).all())

    score_ranges = {'0-4': 0, '6-8': 0, '10-12': 0, '14-16': 0, '18-20': 0}
    for s in sessions:
        if s.score <= 4:    score_ranges['0-4'] += 1
        elif s.score <= 8:  score_ranges['6-8'] += 1
        elif s.score <= 12: score_ranges['10-12'] += 1
        elif s.score <= 16: score_ranges['14-16'] += 1
        else:               score_ranges['18-20'] += 1

    return render_template('admin/stats.html',
                           avg_score=avg_score,
                           best=max(scores) if scores else 0,
                           worst=min(scores) if scores else 0,
                           total=len(sessions),
                           missed_questions=missed,
                           cheat_events=cheat_events,
                           score_ranges=score_ranges)


@admin_bp.route('/export/results')
@login_required
@admin_required
def export_results():
    sessions = QcmSession.query.filter_by(is_completed=True).order_by(QcmSession.end_time.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Étudiant', 'Quiz', 'Note/20', 'Incidents triche', 'Durée (s)', 'Date'])
    for s in sessions:
        writer.writerow([
            s.id, s.user.username,
            s.scheduled_quiz.name if s.scheduled_quiz else 'QCM libre',
            s.score, s.cheat_count,
            int(s.duration_seconds) if s.duration_seconds else '',
            s.end_time.strftime('%Y-%m-%d %H:%M') if s.end_time else ''
        ])
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=resultats_qcm.csv'})


@admin_bp.route('/export/questions')
@login_required
@admin_required
def export_questions():
    questions = Question.query.order_by(Question.category).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['question', 'category', 'difficulty', 'option_a', 'option_b', 'option_c', 'option_d', 'correct'])
    letters = ['a', 'b', 'c', 'd']
    for q in questions:
        opts = sorted(q.options, key=lambda o: o.order)
        correct_letter = next((letters[i] for i, o in enumerate(opts) if o.is_correct), '')
        row = [q.text, q.category, q.difficulty] + [o.text for o in opts] + [''] * (4 - len(opts)) + [correct_letter]
        writer.writerow(row)
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=questions_qcm.csv'})

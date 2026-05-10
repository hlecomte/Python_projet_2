import random
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Question, QcmSession, QcmSessionQuestion, UserAnswer, Option, CheatLog, ScheduledQuiz
from config import Config

student_bp = Blueprint('student', __name__)


@student_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    sessions = (QcmSession.query
                .filter_by(user_id=current_user.id, is_completed=True)
                .order_by(QcmSession.end_time.desc())
                .limit(5).all())

    total_attempts = QcmSession.query.filter_by(user_id=current_user.id, is_completed=True).count()
    avg_score = 0
    if total_attempts > 0:
        all_scores = [s.score for s in QcmSession.query
                      .filter_by(user_id=current_user.id, is_completed=True).all()]
        avg_score = round(sum(all_scores) / len(all_scores), 2)

    now = datetime.utcnow()
    available_quizzes = (ScheduledQuiz.query
                         .filter_by(is_active=True)
                         .filter(ScheduledQuiz.start_time <= now)
                         .filter(ScheduledQuiz.end_time >= now)
                         .order_by(ScheduledQuiz.end_time)
                         .all())

    return render_template('student/dashboard.html',
                           recent_sessions=sessions,
                           total_attempts=total_attempts,
                           avg_score=avg_score,
                           available_quizzes=available_quizzes)


@student_bp.route('/quizzes')
@login_required
def list_quizzes():
    if current_user.is_admin:
        return redirect(url_for('admin.quizzes'))
    now = datetime.utcnow()
    quizzes = (ScheduledQuiz.query
               .filter_by(is_active=True)
               .filter(ScheduledQuiz.end_time >= now)
               .order_by(ScheduledQuiz.start_time)
               .all())
    return render_template('student/quizzes.html', quizzes=quizzes, now=now)


@student_bp.route('/qcm/start')
@login_required
def start_qcm():
    if current_user.is_admin:
        abort(403)

    quiz_id = request.args.get('quiz_id', type=int)
    quiz = None
    question_count = Config.QCM_QUESTION_COUNT

    if quiz_id:
        quiz = ScheduledQuiz.query.get_or_404(quiz_id)
        if not quiz.is_available_now:
            flash("Ce quiz n'est pas disponible actuellement.", 'warning')
            return redirect(url_for('student.list_quizzes'))
        question_count = quiz.question_count

    q_query = Question.query.filter_by(is_active=True)
    if quiz and quiz.category_filter:
        q_query = q_query.filter_by(category=quiz.category_filter)
    if quiz and quiz.difficulty_filter:
        q_query = q_query.filter_by(difficulty=quiz.difficulty_filter)

    available = q_query.count()
    if available < question_count:
        flash(f"Pas assez de questions disponibles ({available} / {question_count} requises).", 'warning')
        return redirect(url_for('student.dashboard'))

    questions = q_query.order_by(db.func.random()).limit(question_count).all()

    session_obj = QcmSession(
        user_id=current_user.id,
        scheduled_quiz_id=quiz.id if quiz else None,
        start_time=datetime.utcnow(),
        total_questions=question_count
    )
    db.session.add(session_obj)
    db.session.flush()

    for i, q in enumerate(questions):
        db.session.add(QcmSessionQuestion(session_id=session_obj.id, question_id=q.id, order=i))

    db.session.commit()
    return redirect(url_for('student.qcm', session_id=session_obj.id))


@student_bp.route('/qcm/<int:session_id>')
@login_required
def qcm(session_id):
    if current_user.is_admin:
        abort(403)

    session_obj = QcmSession.query.get_or_404(session_id)
    if session_obj.user_id != current_user.id:
        abort(403)
    if session_obj.is_completed:
        return redirect(url_for('student.result', session_id=session_id))

    questions_data = []
    for sq in session_obj.session_questions:
        q = sq.question
        options = list(q.options)
        random.shuffle(options)
        questions_data.append({'question': q, 'options': options, 'order': sq.order + 1})

    return render_template('student/qcm.html',
                           session=session_obj,
                           questions_data=questions_data,
                           question_time=Config.QCM_QUESTION_TIME,
                           question_count=session_obj.total_questions)


@student_bp.route('/qcm/<int:session_id>/submit', methods=['POST'])
@login_required
def submit_qcm(session_id):
    if current_user.is_admin:
        abort(403)

    session_obj = QcmSession.query.get_or_404(session_id)
    if session_obj.user_id != current_user.id:
        abort(403)
    if session_obj.is_completed:
        return redirect(url_for('student.result', session_id=session_id))

    end_time = datetime.utcnow()
    elapsed = (end_time - session_obj.start_time).total_seconds()
    max_time = session_obj.total_questions * Config.QCM_QUESTION_TIME + 60

    score = 0.0
    for sq in session_obj.session_questions:
        q = sq.question
        chosen_option_id = request.form.get(f'answer_{q.id}')
        chosen_option = None
        is_correct = False

        if chosen_option_id:
            try:
                chosen_option = Option.query.get(int(chosen_option_id))
                if chosen_option and chosen_option.question_id == q.id:
                    is_correct = chosen_option.is_correct
                else:
                    chosen_option = None
            except (ValueError, TypeError):
                chosen_option = None

        if is_correct:
            score += 2.0

        db.session.add(UserAnswer(
            session_id=session_obj.id,
            question_id=q.id,
            chosen_option_id=chosen_option.id if chosen_option else None,
            is_correct=is_correct
        ))

    session_obj.score = score
    session_obj.end_time = end_time
    session_obj.is_completed = True
    if elapsed > max_time:
        session_obj.time_exceeded = True
        session_obj.cheat_count += 1

    db.session.commit()
    return redirect(url_for('student.result', session_id=session_id))


@student_bp.route('/qcm/<int:session_id>/result')
@login_required
def result(session_id):
    session_obj = QcmSession.query.get_or_404(session_id)
    if session_obj.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    if not session_obj.is_completed:
        return redirect(url_for('student.qcm', session_id=session_id))

    answers_data = []
    for sq in session_obj.session_questions:
        q = sq.question
        user_answer = UserAnswer.query.filter_by(session_id=session_obj.id, question_id=q.id).first()
        answers_data.append({
            'question': q,
            'user_answer': user_answer,
            'correct_option': q.get_correct_option(),
        })

    mention = _get_mention(session_obj.score)
    return render_template('student/result.html',
                           session=session_obj,
                           answers_data=answers_data,
                           mention=mention)


def _get_mention(score):
    if score >= 16: return ('Très Bien', 'success')
    if score >= 14: return ('Bien', 'info')
    if score >= 12: return ('Assez Bien', 'primary')
    if score >= 10: return ('Passable', 'warning')
    return ('Insuffisant', 'danger')


@student_bp.route('/history')
@login_required
def history():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    page = request.args.get('page', 1, type=int)
    sessions = (QcmSession.query
                .filter_by(user_id=current_user.id, is_completed=True)
                .order_by(QcmSession.end_time.desc())
                .paginate(page=page, per_page=10, error_out=False))

    all_scores = [s.score for s in QcmSession.query
                  .filter_by(user_id=current_user.id, is_completed=True).all()]
    avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
    best_score = max(all_scores) if all_scores else 0

    return render_template('student/history.html',
                           sessions=sessions,
                           avg_score=avg_score,
                           best_score=best_score)


@student_bp.route('/log-event', methods=['POST'])
@login_required
def log_event():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error'}), 400

    event_type = data.get('type', 'unknown')[:50]
    session_id = data.get('session_id')

    if session_id:
        session_obj = QcmSession.query.get(session_id)
        if session_obj and session_obj.user_id == current_user.id and not session_obj.is_completed:
            session_obj.cheat_count += 1
            db.session.flush()

    db.session.add(CheatLog(
        user_id=current_user.id,
        session_id=session_id,
        event_type=event_type,
        details=str(data.get('details', ''))[:255]
    ))
    db.session.commit()
    return jsonify({'status': 'logged'}), 200

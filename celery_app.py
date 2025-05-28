from celery import Celery # type: ignore
from app import create_app, send_interactive_message
from project.models import User, Reminder
from datetime import datetime

celery = Celery(__name__, broker='redis://localhost:6379/0')

@celery.task
def disparar_lembretes():
    app = create_app()
    with app.app_context():
        # Buscar lembretes e enviar
        reminders = Reminder.query.all()
        for r in reminders:
            # Lógica de verificação de horário aqui
            user = User.query.get(r.user_id)
            if user.telefone:
                send_interactive_message(user.telefone, r.mensagem)

@celery.task
def disparar_checkin_semanal():
    app = create_app()
    with app.app_context():
        # Se for sábado, dispara check-in
        # etc.
        users = User.query.all()
        for u in users:
            if u.telefone:
                send_interactive_message(u.telefone, "Check-in semanal: responda às perguntas...")

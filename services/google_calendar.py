import os
import uuid
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

def _get_calendar_service():
    """
    Inicializa e retorna o cliente oficial da API Google Calendar se as credenciais existirem.
    """
    if not os.path.exists(settings.GOOGLE_CALENDAR_CREDENTIALS_PATH):
        logger.info("credentials.json não encontrado. Operando em modo de simulação do Google Calendar.")
        return None
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        scopes = ['https://www.googleapis.com/auth/calendar']
        creds = Credentials.from_service_account_file(settings.GOOGLE_CALENDAR_CREDENTIALS_PATH, scopes=scopes)
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Erro ao autenticar no Google Calendar API: {e}")
        return None

class GoogleCalendarService:
    @staticmethod
    def verificar_disponibilidade(data_iso: str) -> List[str]:
        """
        Verifica horários vagos no dia solicitado (formato YYYY-MM-DD).
        """
        service = _get_calendar_service()
        horarios_padrao = ["09:00", "10:30", "14:00", "15:30", "17:00"]
        
        if not service:
            return horarios_padrao
        
        try:
            time_min = f"{data_iso}T08:00:00-03:00"
            time_max = f"{data_iso}T18:00:00-03:00"
            events_result = service.events().list(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            horarios_ocupados = []
            for ev in events:
                st = ev['start'].get('dateTime', '')
                if 'T' in st:
                    horarios_ocupados.append(st.split('T')[1][:5])
            
            disponiveis = [h for h in horarios_padrao if h not in horarios_ocupados]
            return disponiveis if disponiveis else ["14:00", "16:00"]
        except Exception as e:
            logger.error(f"Erro ao listar eventos do Google Calendar: {e}")
            return horarios_padrao

    @staticmethod
    def agendar_visita_tecnica(summary: str, description: str, start_iso: str, end_iso: str) -> Dict[str, Any]:
        """
        Cria um evento de medição técnica no Google Calendar.
        """
        service = _get_calendar_service()
        event_id = f"GCAL-{uuid.uuid4().hex[:10]}"
        
        if not service:
            logger.info(f"[SIMULAÇÃO GCAL] Visita agendada: {summary} das {start_iso} até {end_iso}")
            return {
                "status": "sucesso",
                "event_id": event_id,
                "summary": summary,
                "start": start_iso,
                "end": end_iso,
                "mensagem": "Visita técnica agendada com sucesso no Google Agenda (Modo Simulação)."
            }
        
        try:
            event_body = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start_iso, 'timeZone': settings.TIMEZONE},
                'end': {'dateTime': end_iso, 'timeZone': settings.TIMEZONE},
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 120},
                    ],
                },
            }
            created_event = service.events().insert(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                body=event_body
            ).execute()
            
            return {
                "status": "sucesso",
                "event_id": created_event.get('id'),
                "summary": summary,
                "start": start_iso,
                "end": end_iso,
                "link": created_event.get('htmlLink'),
                "mensagem": "Visita técnica agendada com sucesso no Google Agenda!"
            }
        except Exception as e:
            logger.error(f"Erro ao agendar no Google Calendar: {e}")
            return {
                "status": "erro",
                "event_id": event_id,
                "mensagem": f"Falha no agendamento: {str(e)}"
            }

    @staticmethod
    def atualizar_agendamento(event_id: str, new_start_iso: str, new_end_iso: str) -> Dict[str, Any]:
        """
        Remarca o horário de uma visita técnica.
        """
        service = _get_calendar_service()
        if not service or event_id.startswith("GCAL-"):
            return {"status": "sucesso", "event_id": event_id, "mensagem": f"Agendamento {event_id} remarcado para {new_start_iso}."}
        
        try:
            event = service.events().get(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=event_id).execute()
            event['start'] = {'dateTime': new_start_iso, 'timeZone': settings.TIMEZONE}
            event['end'] = {'dateTime': new_end_iso, 'timeZone': settings.TIMEZONE}
            updated_event = service.events().update(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=event_id, body=event).execute()
            return {"status": "sucesso", "event_id": updated_event.get('id'), "mensagem": "Agendamento remarcado no Google Agenda!"}
        except Exception as e:
            return {"status": "erro", "mensagem": f"Erro ao atualizar agendamento: {e}"}

    @staticmethod
    def cancelar_agendamento(event_id: str) -> Dict[str, Any]:
        """
        Cancela o evento no Google Calendar.
        """
        service = _get_calendar_service()
        if not service or event_id.startswith("GCAL-"):
            return {"status": "sucesso", "event_id": event_id, "mensagem": f"Agendamento {event_id} cancelado com sucesso."}
        
        try:
            service.events().delete(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=event_id).execute()
            return {"status": "sucesso", "event_id": event_id, "mensagem": "Agendamento removido do Google Agenda."}
        except Exception as e:
            return {"status": "erro", "mensagem": f"Erro ao cancelar agendamento: {e}"}

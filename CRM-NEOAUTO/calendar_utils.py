import os
import datetime
from googleapiclient.discovery import build
from pathlib import Path

# --- CONFIGURACIÓN ---
TIME_ZONE = 'America/Lima'

def create_calendar_event(creds, summary, location, start_dt, lead_name="Lead"):
    """
    Crea un evento en Google Calendar.
    Args:
        creds: Credenciales autorizadas de Google.
        summary: Título del evento.
        location: Dirección o lugar de la cita.
        start_dt: Objeto datetime (naive o con timezone) para el inicio.
        lead_name: Nombre para la descripción.
    """
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Calcular fin (1 hora después)
        end_dt = start_dt + datetime.timedelta(hours=1)
        
        event = {
            'summary': summary,
            'location': location,
            'description': f'Cita agendada desde el CRM NeoAuto para el lead: {lead_name}',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': TIME_ZONE,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': TIME_ZONE,
            },
            'attendees': [
                {'email': 'rich@kaizencapital.pe'},
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 15},
                ],
            },
        }

        event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        return event.get('htmlLink')

    except Exception as e:
        print(f"Error creando evento en Calendar: {e}")
        return None

"""
Fire-and-forget HTTP calls to the Notification service.
Never raises — failures are logged and ignored so they never break the main request.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# KPI thresholds — send alert if a metric drops below these values
KPI_THRESHOLDS = {
    'fungicide_reduction': ('below', 10,   'Fungicide Reduction', '%'),
    'fuel_reduction':      ('below', 5,    'Fuel Reduction',      '%'),
    'co2_reduction':       ('below', 30,   'CO₂ Reduction',       ' kg'),
    'yield_reduction':     ('below', -5.0, 'Yield Change',        '%'),
}


def _url(path: str) -> str:
    base = getattr(settings, 'NOTIFICATION_SERVICE_URL', 'http://localhost:8001')
    return f"{base.rstrip('/')}{path}"


def notify(template_name: str, recipient: str, parameters: dict) -> None:
    """Send a notification email. Fire-and-forget — never raises."""
    if not recipient:
        return
    try:
        resp = requests.post(
            _url('/api/send/'),
            json={'template_name': template_name, 'recipient': recipient, 'parameters': parameters},
            timeout=5,
        )
        if resp.status_code == 200:
            logger.info(f"[NOTIFY] Sent '{template_name}' to {recipient}")
        else:
            logger.warning(f"[NOTIFY] '{template_name}' → {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"[NOTIFY] Failed to send '{template_name}' to {recipient}: {e}")


# ── Convenience helpers called from views ─────────────────────────────────────

def notify_flight_added(user, block, flight):
    notify('flight_added', user.email, {
        'user_name':      user.get_full_name() or user.username,
        'block_name':     block.name,
        'farm_name':      block.farm.name,
        'flight_date':    str(flight.flight_date),
        'altitude_meters': str(flight.altitude_meters) if flight.altitude_meters else 'N/A',
    })


def notify_kpi_added(user, block, kpi):
    notify('kpi_added', user.email, {
        'user_name':            user.get_full_name() or user.username,
        'block_name':           block.name,
        'farm_name':            block.farm.name,
        'period':               kpi.period,
        'fungicide_reduction':  str(kpi.fungicide_reduction) if kpi.fungicide_reduction is not None else 'N/A',
        'fuel_reduction':       str(kpi.fuel_reduction)      if kpi.fuel_reduction      is not None else 'N/A',
        'co2_reduction':        str(kpi.co2_reduction)       if kpi.co2_reduction       is not None else 'N/A',
        'yield_reduction':      str(kpi.yield_reduction)     if kpi.yield_reduction     is not None else 'N/A',
    })
    # Check thresholds and send alert for each metric that fails
    for field, (direction, threshold, label, unit) in KPI_THRESHOLDS.items():
        value = getattr(kpi, field, None)
        if value is None:
            continue
        triggered = float(value) < threshold if direction == 'below' else float(value) > threshold
        if triggered:
            notify('kpi_alert', user.email, {
                'user_name':   user.get_full_name() or user.username,
                'block_name':  block.name,
                'farm_name':   block.farm.name,
                'period':      kpi.period,
                'metric_name': label,
                'value':       f"{value}{unit}",
                'threshold':   f"{threshold}{unit}",
            })


def notify_action_performed(user, block, action):
    notify('action_performed', user.email, {
        'user_name':    user.get_full_name() or user.username,
        'block_name':   block.name,
        'farm_name':    block.farm.name,
        'action_type':  action.action_type,
        'chemical_type': action.chemical_type or 'NONE',
        'period':       action.period,
        'quantity':     f"{action.quantity} L/kg" if action.quantity else 'N/A',
        'cost':         f"€{action.cost}"         if action.cost     else 'N/A',
        'notes':        action.notes or '—',
    })


def notify_phenology_stage_added(user, block, stage):
    notify('phenology_stage_added', user.email, {
        'user_name':  user.get_full_name() or user.username,
        'block_name': block.name,
        'farm_name':  block.farm.name,
        'stage_name': stage.stage_name,
        'start_date': str(stage.start_date),
        'end_date':   str(stage.end_date) if stage.end_date else 'Ongoing',
        'notes':      stage.notes or '—',
    })

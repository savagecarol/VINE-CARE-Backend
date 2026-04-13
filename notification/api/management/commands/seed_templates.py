from django.core.management.base import BaseCommand
from api.models import NotificationTemplate

TEMPLATES = [
    {
        'name': 'flight_added',
        'subject': '✈️ Flight Added — {{block_name}}',
        'is_html': True,
        'body': """<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f3;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <!-- Header -->
      <tr><td style="background:#111611;padding:24px 32px;">
        <p style="margin:0;color:#A4CF9C;font-size:13px;letter-spacing:2px;text-transform:uppercase;">VineCare</p>
        <h1 style="margin:4px 0 0;color:#ffffff;font-size:22px;font-weight:600;">Flight Successfully Added</h1>
      </td></tr>
      <!-- Body -->
      <tr><td style="padding:32px;">
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">Hello <strong>{{user_name}}</strong>,</p>
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">A new drone flight has been recorded in VineCare.</p>
        <!-- Details card -->
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;border-radius:8px;padding:20px;margin-bottom:24px;">
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;width:140px;">Block</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;font-weight:600;">{{block_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Farm</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{farm_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Flight Date</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{flight_date}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Altitude</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{altitude_meters}} m</td>
          </tr>
        </table>
        <p style="color:#6B7280;font-size:13px;margin:0;">Images will be processed and results will be available shortly.</p>
      </td></tr>
      <!-- Footer -->
      <tr><td style="background:#f4f6f3;padding:20px 32px;text-align:center;">
        <p style="color:#9CA3AF;font-size:12px;margin:0;">© VineCare Platform · Automated Notification</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>""",
    },
    {
        'name': 'kpi_added',
        'subject': '📊 KPI Record Added — {{block_name}} ({{period}})',
        'is_html': True,
        'body': """<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f3;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <tr><td style="background:#111611;padding:24px 32px;">
        <p style="margin:0;color:#A4CF9C;font-size:13px;letter-spacing:2px;text-transform:uppercase;">VineCare</p>
        <h1 style="margin:4px 0 0;color:#ffffff;font-size:22px;font-weight:600;">KPI Record Added</h1>
      </td></tr>
      <tr><td style="padding:32px;">
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">Hello <strong>{{user_name}}</strong>,</p>
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">A new KPI record has been saved for <strong>{{block_name}}</strong> — Period <strong>{{period}}</strong>.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;border-radius:8px;padding:20px;margin-bottom:24px;">
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;width:180px;">Block</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;font-weight:600;">{{block_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Farm</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{farm_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Period</td>
            <td style="padding:6px 0;color:#4B6646;font-size:13px;font-weight:600;">{{period}}</td>
          </tr>
          <tr><td colspan="2" style="padding-top:12px;border-top:1px solid #E5E7EB;"></td></tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Fungicide Reduction</td>
            <td style="padding:6px 0;color:#4B6646;font-size:13px;font-weight:600;">{{fungicide_reduction}}%</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Fuel Reduction</td>
            <td style="padding:6px 0;color:#6B9E8B;font-size:13px;font-weight:600;">{{fuel_reduction}}%</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">CO₂ Reduction</td>
            <td style="padding:6px 0;color:#2563EB;font-size:13px;font-weight:600;">{{co2_reduction}} kg</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Yield Change</td>
            <td style="padding:6px 0;color:#F59E0B;font-size:13px;font-weight:600;">{{yield_reduction}}%</td>
          </tr>
        </table>
      </td></tr>
      <tr><td style="background:#f4f6f3;padding:20px 32px;text-align:center;">
        <p style="color:#9CA3AF;font-size:12px;margin:0;">© VineCare Platform · Automated Notification</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>""",
    },
    {
        'name': 'kpi_alert',
        'subject': '⚠️ KPI Alert — {{metric_name}} below threshold ({{block_name}})',
        'is_html': True,
        'body': """<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f3;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <tr><td style="background:#7F1D1D;padding:24px 32px;">
        <p style="margin:0;color:#FCA5A5;font-size:13px;letter-spacing:2px;text-transform:uppercase;">VineCare · Alert</p>
        <h1 style="margin:4px 0 0;color:#ffffff;font-size:22px;font-weight:600;">⚠️ KPI Below Threshold</h1>
      </td></tr>
      <tr><td style="padding:32px;">
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">Hello <strong>{{user_name}}</strong>,</p>
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">A KPI metric is below the expected threshold for <strong>{{block_name}}</strong>.</p>
        <!-- Alert box -->
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:20px;margin-bottom:24px;">
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;width:160px;">Block</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;font-weight:600;">{{block_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Farm</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{farm_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Period</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{period}}</td>
          </tr>
          <tr><td colspan="2" style="padding-top:12px;border-top:1px solid #FECACA;"></td></tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Metric</td>
            <td style="padding:6px 0;color:#DC2626;font-size:14px;font-weight:700;">{{metric_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Recorded Value</td>
            <td style="padding:6px 0;color:#DC2626;font-size:14px;font-weight:700;">{{value}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Threshold</td>
            <td style="padding:6px 0;color:#374151;font-size:13px;">{{threshold}}</td>
          </tr>
        </table>
        <p style="color:#6B7280;font-size:13px;margin:0;">Please review the block and take corrective action if needed.</p>
      </td></tr>
      <tr><td style="background:#f4f6f3;padding:20px 32px;text-align:center;">
        <p style="color:#9CA3AF;font-size:12px;margin:0;">© VineCare Platform · Automated Alert</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>""",
    },
    {
        'name': 'action_performed',
        'subject': '🌿 Action Recorded — {{action_type}} on {{block_name}}',
        'is_html': True,
        'body': """<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f3;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <tr><td style="background:#111611;padding:24px 32px;">
        <p style="margin:0;color:#A4CF9C;font-size:13px;letter-spacing:2px;text-transform:uppercase;">VineCare</p>
        <h1 style="margin:4px 0 0;color:#ffffff;font-size:22px;font-weight:600;">Action Recorded</h1>
      </td></tr>
      <tr><td style="padding:32px;">
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">Hello <strong>{{user_name}}</strong>,</p>
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">A vineyard action has been logged in VineCare.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;border-radius:8px;padding:20px;margin-bottom:24px;">
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;width:160px;">Block</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;font-weight:600;">{{block_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Farm</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{farm_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Action</td>
            <td style="padding:6px 0;color:#4B6646;font-size:13px;font-weight:700;">{{action_type}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Chemical</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{chemical_type}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Period</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{period}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Quantity</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{quantity}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Cost</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{cost}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;vertical-align:top;">Notes</td>
            <td style="padding:6px 0;color:#374151;font-size:13px;">{{notes}}</td>
          </tr>
        </table>
      </td></tr>
      <tr><td style="background:#f4f6f3;padding:20px 32px;text-align:center;">
        <p style="color:#9CA3AF;font-size:12px;margin:0;">© VineCare Platform · Automated Notification</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>""",
    },
    {
        'name': 'phenology_stage_added',
        'subject': '🌱 Phenology Stage Recorded — {{stage_name}} ({{block_name}})',
        'is_html': True,
        'body': """<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f6f3;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <tr><td style="background:#111611;padding:24px 32px;">
        <p style="margin:0;color:#A4CF9C;font-size:13px;letter-spacing:2px;text-transform:uppercase;">VineCare</p>
        <h1 style="margin:4px 0 0;color:#ffffff;font-size:22px;font-weight:600;">Phenology Stage Recorded</h1>
      </td></tr>
      <tr><td style="padding:32px;">
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">Hello <strong>{{user_name}}</strong>,</p>
        <p style="color:#374151;font-size:15px;margin:0 0 24px;">A new phenology stage has been recorded for <strong>{{block_name}}</strong>.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f3;border-radius:8px;padding:20px;margin-bottom:24px;">
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;width:160px;">Block</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;font-weight:600;">{{block_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Farm</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{farm_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Stage</td>
            <td style="padding:6px 0;color:#4B6646;font-size:14px;font-weight:700;">{{stage_name}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">Start Date</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{start_date}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;">End Date</td>
            <td style="padding:6px 0;color:#111611;font-size:13px;">{{end_date}}</td>
          </tr>
          <tr>
            <td style="padding:6px 0;color:#6B7280;font-size:13px;vertical-align:top;">Notes</td>
            <td style="padding:6px 0;color:#374151;font-size:13px;">{{notes}}</td>
          </tr>
        </table>
      </td></tr>
      <tr><td style="background:#f4f6f3;padding:20px 32px;text-align:center;">
        <p style="color:#9CA3AF;font-size:12px;margin:0;">© VineCare Platform · Automated Notification</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>""",
    },
]


class Command(BaseCommand):
    help = 'Seed email templates for all VineCare notification events'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for t in TEMPLATES:
            obj, is_new = NotificationTemplate.objects.update_or_create(
                name=t['name'],
                defaults={
                    'subject': t['subject'],
                    'body':    t['body'],
                    'is_html': t['is_html'],
                    'is_active': True,
                },
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {t["name"]}'))
            else:
                updated += 1
                self.stdout.write(f'  Updated: {t["name"]}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone — {created} created, {updated} updated.'
        ))

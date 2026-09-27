"""Run every five minutes on the host: flask --app run credits maintain."""
import json
import os
from pathlib import Path
from datetime import timedelta
import click
from flask.cli import with_appcontext
from .credit_cli import credits
from .models import db, Subscription, PayPalWebhookEvent
from .credit_models import SubscriptionCheckout, CreditSystemState
from .subscription_checkout import sync_one, _create_remote
from .subscription_credits import PayPal, utcnow, iso, credit_day, plans, setting, parse_time


@credits.command('maintain')
@click.option('--output', required=True, type=click.Path(dir_okay=False), help='New private report filename.')
@with_appcontext
def maintain(output):
    """Apply verified recent payments; retry saved checkout/upgrade work. No full inventory scan."""
    target = Path(output)
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    report = {'started_at': iso(utcnow()), 'checkouts': [], 'subscriptions': []}
    api = PayPal()
    def save():
        temp = target.with_suffix(target.suffix + '.tmp')
        with os.fdopen(os.open(temp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600), 'w') as handle:
            json.dump(report, handle, indent=2, default=str)
        os.replace(temp, target)
    attempts = [r.id for r in SubscriptionCheckout.query.filter(
        SubscriptionCheckout.paypal_subscription_id.is_(None),
        SubscriptionCheckout.state.in_(['creating', 'pending', 'review'])).all()]
    db.session.rollback()
    for attempt_id in attempts:
        item = {'checkout_id': attempt_id}
        try:
            item['subscription_id'] = _create_remote(attempt_id, api)
            item['result'] = 'recovered'
        except Exception as exc:
            db.session.rollback()
            item.update(result='needs_review_or_retry', error=type(exc).__name__)
        report['checkouts'].append(item)
        save()
    ids = {s.paypal_subscription_id for s in Subscription.query.filter(db.or_(
        Subscription.status.in_(['active', 'pending', 'suspended']),
        Subscription.expiry_date >= credit_day(),
        Subscription.created_at >= utcnow()-timedelta(days=35))).all()}
    ids.update(r.paypal_subscription_id for r in SubscriptionCheckout.query.filter_by(state='cancel_pending').all()
               if r.paypal_subscription_id)
    ids.update(h.paypal_subscription_id for h in PayPalWebhookEvent.query.filter(
        PayPalWebhookEvent.status.in_(['failed', 'review', 'received'])).all()
               if h.paypal_subscription_id and h.paypal_subscription_id.startswith('I-'))
    db.session.rollback()
    for sid in sorted(ids):
        try:
            item = sync_one(sid, api=api)
            item['result'] = 'checked'
        except Exception as exc:
            db.session.rollback()
            item = {'subscription_id': sid, 'result': 'needs_review_or_retry', 'error': type(exc).__name__}
        report['subscriptions'].append(item)
        save()
    report['finished_at'] = iso(utcnow())
    report['needs_attention'] = sum(
        i.get('result') == 'needs_review_or_retry' or i.get('upgrade_pending', False) or i.get('payment_review_required', False)
        for i in report['subscriptions'] + report['checkouts'])
    save()
    click.echo(f"Checked {len(ids)} subscriptions; {report['needs_attention']} need review/retry. Report: {target}")
    if report['needs_attention']:
        raise click.ClickException('Review the maintenance report; verified repairs were committed.')


@credits.command('doctor')
@with_appcontext
def doctor():
    """Check local prerequisites. Does not call PayPal or change accounts."""
    from sqlalchemy import inspect
    required = {'subscription_checkout', 'subscription_credit_receipt', 'credit_system_state'}
    missing = required - set(inspect(db.engine).get_table_names())
    if missing:
        raise click.ClickException('Run the migration. Missing tables: ' + ', '.join(sorted(missing)))
    marker = db.session.get(CreditSystemState, 'atomic_issuance_started_at')
    if not marker:
        raise click.ClickException('Previous credit migration/cutover marker is missing. Do not enable checkout yet.')
    parse_time(marker.value)
    plans()
    for name in ('PAYPAL_CLIENT_ID', 'PAYPAL_SECRET', 'PAYPAL_WEBHOOK_ID'):
        if not setting(name):
            raise click.ClickException('Missing setting: ' + name)
    click.echo('Local schema/settings present. Verify webhook delivery and checkout in PayPal sandbox before going live.')

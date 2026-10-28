# Subscription release candidate — October 9, 2026

This is the single deployment set for the fixes developed in this conversation.
It includes the Windows report-lock fix and the compatible checkout module.
Local validation: 62 tests passed with SQLite and simulated PayPal. The earlier
real maintenance run issued 28 credits across five accounts. Neither result
proves production webhook delivery, host scheduling, or concurrent writes on
the live database engine. Production readiness is still pending those checks.

## Exactly what to copy

Extract the ZIP first. Back up the current application files. Copy these files
to the listed locations in your existing project; keep the filenames exact.

| ZIP file | Destination |
| --- | --- |
| app/views.py | Existing app/views.py |
| app/subscription_checkout.py | Existing app/subscription_checkout.py |
| app/subscription_credits.py | Existing app/subscription_credits.py |
| app/subscription_maintenance.py | Existing app/subscription_maintenance.py |
| app/credit_routes.py | Existing app/credit_routes.py |
| schedule_subscription_maintenance.py | Project root beside run.py |
| verify_subscription_release.py | Project root beside run.py |

The first six are the coordinated application files. The seventh is a read-only
file verifier. RELEASE_CHECKS.md is this instruction document. This deployment
ZIP contains no baseline, model fixtures, alternate application copies, or tests.
Keep your existing credit_cli.py, credit_models.py, models.py, run.py, application
factory, config, .env, migrations, templates, and static files. The previous
receipt/state/checkout migrations and CLI registrations remain prerequisites;
this release introduces no new database migration.

This is based on the October 9 uploads plus the corrected checkout file already
delivered. views.py retains the complete previously audited file. The latest
changes affect report writing, compatibility checks, and error diagnostics;
they do not change credit amounts, expiry rules, or ownership requirements.

## Windows checks now

Your Windows app uses LIVE PayPal and the LIVE database. The commands below
are read-only except the separately identified maintenance command.

In the project directory, with its virtual environment active, run:

```bat
python verify_subscription_release.py
```

It must report that all six application files match. It reads file contents
without importing the app or accessing the database/network. It tolerates
Windows line endings. A mismatch means inspect/install the matching file;
do not remove the check or overwrite newer unrelated work blindly.

Then run:

```bat
python -m flask --app run credits doctor
```

Doctor now rejects an incompatible sync_one signature and checks all seven
subscription route delegates, including the webhook and confirmation routes.
Doctor reads local schema/configuration; it does not call PayPal, verify that
credentials actually work, or prove webhook delivery.

Do not simulate purchases, cancels, upgrades, or fake webhooks using this live
database. The optional regression ZIP runs isolated SQLite tests with fake
PayPal responses and does not import run.py or load your .env.

For future manual maintenance, type these commands separately in the same CMD
window. The first sets report location for that session; the second MUTATES
live accounts by applying verified missing payments and authorized recoveries.

```bat
set "CREDIT_REPORT_DIR=%LOCALAPPDATA%\PickupVolleyballPDX\credit_reports"
```

```bat
python schedule_subscription_maintenance.py
```

Use the actual report path printed by Python. Microsoft Store Python may map
LOCALAPPDATA into its LocalCache. A nonzero result with review items can occur
after successful repairs. Inspect credits_issued, individual errors/payments,
finished_at, and coverage_errors. Earlier commits survive a later report error.

## What the new diagnostics establish

- Before any account processing, an incompatible checkout signature fails with
  a clear message. It cannot produce another 66-row unexpected-keyword failure.
- Webhook errors record their stage: signature verification, subscription lookup,
  transaction lookup, subscription sync, credit issuance, commit, or upgrade.
- API errors identify the HTTP method and endpoint as well as status/category.
- Database integrity failures record the driver exception type and numeric
  error code when available. SQL parameters, response bodies, credentials, and
  tokens are not added to these diagnostics.
- Temporary Windows report replacement locks are retried. Persistent failure
  preserves the latest complete temporary snapshot and reports a local file
  error; discovery no longer mislabels that report-write error as PayPal failure.

These diagnostics cannot reconstruct the exception suppressed on October 3.
The confirmed sequence for Alua was a successful payment, failed webhook
processing 11 seconds later, and credit issuance about 4.5 days later. The
signature mismatch discovered October 9 was a separate maintenance problem.

## Evidence required before declaring production reliable

1. On the VPS, identify the actual application directory, service, Python
   environment, database target, and scheduling mechanism. Inspect with pwd and
   crontab -l first; an empty user crontab does not rule out another user's job,
   a system-wide cron entry, or a systemd timer. Do not publish until the intended
   directory/service is known and a reviewed file/database backup exists.
2. When you choose to deploy, install this same coordinated set on the VPS,
   run the file verifier and doctor there, and restart the actual application
   service. Updating Windows alone does not update production webhook handling.
3. Verify the PayPal live app's configured webhook ID and endpoint refer to this
   production app and /api/paypal/webhook. Observe an authentic payment webhook
   or an authorized resend of an already-paid event. Record its response and
   detailed failure note if it fails. Verify one payment maps to one grant and
   receipt; redelivery of that event must not increase credits again.
4. Verify automatic recovery on the VPS, not just a manually invoked script.
   Schedule the wrapper every five minutes using the actual absolute project
   path and virtual-environment Python. Inspect two separate scheduled runs,
   their completion times, exit codes, and reports. A cron entry alone does not
   prove the job ran. Configure persistent CREDIT_REPORT_DIR if desired; the
   Windows CMD setting does not transfer to the VPS or a new shell.
5. Route worker failures and stale completion (over the configured threshold)
   into the host's real monitoring/alert mechanism. Check both freshness and
   unresolved review counts. Existing historical review items must be triaged;
   do not suppress them merely to make a green status.
6. Test concurrency using an isolated database of the same engine as production
   and PayPal sandbox credentials before claiming concurrent-write coverage.
   SQLite tests here validate transaction rollback and serial duplicate handling,
   but do not prove MySQL/PostgreSQL locking under concurrent webhook delivery.

Do not claim a five-minute recovery guarantee solely because cron runs every
five minutes: PayPal availability, long-running scans, and unresolved ownership
can still delay recovery. The wrapper prevents overlap; its actual completion
times and failures must be monitored.

## Outstanding member/account work

The October 9 22:05 UTC maintenance run issued 28 credits. It left 50 flags:
24 HTTP 404 lookups, 18 legacy receipt/grant linkage reviews, five refunded
payments, one HELD payment, and two ownership failures. Alua's October payment
was already linked and did not receive a duplicate grant. Her September payment
was outside that run's 32-day window; its earlier linkage warning was not fixed
by falling out of the window.

No new PayPal inventory scan occurred in that pass (inventory_checked=false).
Alua's reported re-subscription is still unverified because the earlier
discovery attempt was incomplete. A new, completed audit/discovery is needed
before drawing conclusions about any additional agreement.

Review older grants and spending before authorizing a legacy restoration. Do
not manufacture credits for refunded/held transactions, treat a 404 as a
cancellation, or guess ownership from an email/name resemblance.

## Test evidence

62 checks passed on October 9 using Python 3.12, SQLite, and simulated PayPal.
The suite covers original regressions, full views import, original template
rendering, preserved unrelated routes, signup retry/idempotency, add-both-tiers,
payment-first upgrades, durable cancellation retries beyond the payment scan,
retired-agreement signup, ownership checks, legacy repair safeguards, atomic
rollback, report locks, and maintenance freshness.

New webhook checks cover unavailable transaction history then retry; duplicate
delivery; failed webhook followed by maintenance then redelivery; integrity
failure during issuance followed by retry; invalid signature rejection; and
cancellation before delayed payment delivery without reactivating the agreement.
Diagnostic tests check that HTTP bodies, tokens, and SQL parameters are absent.

These are automated simulations, not a real browser/PayPal end-to-end test.
Native Windows locking, production-engine concurrency, actual PayPal delivery,
production scheduler execution, and alert delivery remain unverified here.

from app import create_app, db
from app.models import User, Subscription, EventAttendee, CreditGrant
from datetime import date, timedelta, datetime

app = create_app()

def run_credit_restoration():
    reference_date = date.today()
    print(f"--- STARTING CREDIT RESTORATION ---")
    print(f"Reference Date: {reference_date}\n")

    users_updated = 0

    with app.app_context():
        # 1. Find all subscriptions (active or canceled) that haven't expired yet
        valid_subs = Subscription.query.filter(
            Subscription.expiry_date >= reference_date
        ).all()

        for sub in valid_subs:
            user = User.query.get(sub.user_id)
            if not user:
                continue

            # --- THE DOUBLE-DIP CHECK ---
            # Checks if a grant already exists for this specific expiry date.
            existing_grant = CreditGrant.query.filter(
                CreditGrant.user_id == user.id,
                CreditGrant.expiry_date == sub.expiry_date
            ).first()

            if existing_grant:
                continue

            # --- CALCULATION LOGIC ---
            # Window: 30 days before the expiry
            cycle_start_date = sub.expiry_date - timedelta(days=30)
            cycle_start_dt = datetime.combine(cycle_start_date, datetime.min.time())

            # Tier Allocation
            initial_credits = 8 if sub.tier == 2 else 4
            
            # Count RSVPs made within this window
            rsvps_in_cycle = EventAttendee.query.filter(
                EventAttendee.user_id == user.id,
                EventAttendee.timestamp >= cycle_start_dt
            ).count()

            calculated_balance = initial_credits - rsvps_in_cycle

            if calculated_balance > 0:
                print(f"RESTORING: {user.first_name} {user.last_name}")
                print(f"  - Granting {calculated_balance} credits (Exp: {sub.expiry_date})")

                # --- CORRECTED DATABASE WRITE ---
                new_grant = CreditGrant(
                    user_id=user.id,
                    balance=calculated_balance,     # Correct field from models.py
                    source_type='subscription',     # Required field
                    description=f"Restored Credits (Cycle {cycle_start_date} to {sub.expiry_date})",
                    expiry_date=sub.expiry_date
                )
                
                db.session.add(new_grant)
                users_updated += 1

        # Commit all changes at once
        if users_updated > 0:
            db.session.commit()
            print("-" * 50)
            print(f"SUCCESS: Restored credits for {users_updated} users.")
        else:
            print("No users found who need credits restored.")

if __name__ == "__main__":
    run_credit_restoration()
from app import create_app, db
from app.models import User, Subscription, CreditGrant, EventAttendee
from datetime import date, timedelta, datetime

# Initialize the Flask application context
app = create_app()

def audit_and_fix():
    print("--- STARTING SMART SUBSCRIPTION FIX (LIVE RUN) ---")
    
    with app.app_context():
        today = date.today()
        
        # 1. Find all subscriptions that are "Active" but have an "Old" expiry date
        stuck_subs = Subscription.query.filter(
            Subscription.status == 'active', 
            Subscription.expiry_date < today
        ).all()

        print(f"Found {len(stuck_subs)} stuck subscriptions.")
        print("-" * 60)

        count = 0
        changes_made = 0

        for sub in stuck_subs:
            user = User.query.get(sub.user_id)
            if not user:
                print(f"Skipping subscription {sub.id}: User not found.")
                continue

            # --- 1. DETERMINE THE "GAP" PERIOD ---
            gap_start_date = sub.expiry_date
            gap_start_dt = datetime.combine(gap_start_date, datetime.min.time())
            
            # --- 2. COUNT USAGE IN THE GAP ---
            # Count how many times they RSVP'd since they technically expired
            rsvps_in_gap = EventAttendee.query.filter(
                EventAttendee.user_id == user.id,
                EventAttendee.timestamp >= gap_start_dt
            ).count()

            # --- 3. CALCULATE NET CREDITS ---
            initial_credits = sub.credits_per_month  # e.g., 4 or 8
            
            # Deduct any games they played during the "stuck" period
            credits_to_add = max(0, initial_credits - rsvps_in_gap)

            # --- 4. NEW DATES ---
            # Reset billing cycle to start TODAY
            new_expiry = today + timedelta(days=30)
            # Give credits a 45-day buffer
            credit_expiry_date = today + timedelta(days=45)

            print(f"User: {user.first_name} {user.last_name} ({user.email})")
            print(f"  Stuck Since:    {sub.expiry_date} (Used {rsvps_in_gap} events in gap)")
            print(f"  New Expiry:     {new_expiry}")
            print(f"  Credits Adding: {credits_to_add} (Expires: {credit_expiry_date})")
            print("-" * 60)

            # --- THE FIX LOGIC (Uncommented & Active) ---
            
            # 1. Update Subscription Date
            sub.expiry_date = new_expiry
            
            # 2. Add Credits (Only if they are owed any)
            if credits_to_add > 0:
                new_grant = CreditGrant(
                    user_id=user.id,
                    balance=credits_to_add,
                    source_type='subscription',
                    description=f'Renewal Correction (Less {rsvps_in_gap} past events)',
                    expiry_date=credit_expiry_date
                )
                db.session.add(new_grant)
            
            count += 1
            changes_made += 1

        print(f"Processed {count} users.")
        
        # --- COMMIT CHANGES ---
        if changes_made > 0:
            db.session.commit()
            print("SUCCESS: Database has been updated.")
        else:
            print("No changes were necessary.")

if __name__ == "__main__":
    audit_and_fix()
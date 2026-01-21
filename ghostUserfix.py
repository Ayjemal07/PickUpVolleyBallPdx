from app.models import User, Subscription, db
from datetime import date, timedelta

# ================= CONFIGURATION =================
THE_MISSING_PAYPAL_ID = "I-XXXXXXXXXXXXXXXX"  # <--- PASTE REAL PAYPAL ID
USER_EMAIL = "user@example.com"               # <--- PASTE REAL EMAIL
TIER_LEVEL = 1                                # <--- Set to 1 or 2
# =================================================

# Logic to determine credits
if TIER_LEVEL == 1:
    CREDITS_TO_GIVE = 4
elif TIER_LEVEL == 2:
    CREDITS_TO_GIVE = 8
else:
    raise ValueError("Invalid Tier Level! Must be 1 or 2.")

# Find the user
user = User.query.filter_by(email=USER_EMAIL).first()

if user:
    print(f"Found user: {user.first_name} {user.last_name}")
    print(f"Applying Tier {TIER_LEVEL} Subscription ({CREDITS_TO_GIVE} Credits/Month)...")
    
    # Create the missing subscription record
    new_sub = Subscription(
        user_id=user.id,
        paypal_subscription_id=THE_MISSING_PAYPAL_ID,
        tier=TIER_LEVEL,
        credits_per_month=CREDITS_TO_GIVE,
        status='active',
        expiry_date=date.today() + timedelta(days=30)
    )
    
    db.session.add(new_sub)
    db.session.commit()
    
    print(f"SUCCESS! Linked subscription {THE_MISSING_PAYPAL_ID} to {user.first_name} {user.last_name} ({user.email}) at Tier {TIER_LEVEL}.")
else:
    print(f"ERROR: User with email '{USER_EMAIL}' not found.")
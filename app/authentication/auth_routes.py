# app/authentication/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, session
from app.forms import UserLoginForm, UserRegistrationForm
from ..models import User, Subscription, db
from flask_login import login_user, logout_user, login_required
from flask import request
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import re
from datetime import date, datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import base64
import io
from reportlab.lib.utils import ImageReader


import uuid
from werkzeug.utils import secure_filename
import os
from flask import current_app
from flask_login import current_user
mail = Mail()
serializer = URLSafeTimedSerializer('your-secret-key')  # Replace with your secret key


auth = Blueprint('auth', __name__, template_folder='auth_templates')


def send_underage_rejection_email(user_email):
    """Sends an email to users who are not old enough to register."""
    msg = Message(
        subject="Registration Rejected: Age Requirement",
        recipients=[user_email],
        body="Thank you for your interest in Pick Up Volleyball PDX. At this time, we are only able to accept registrations from individuals who are 18 years or older. We were unable to create your account as a result of this policy. You may have a parent/legal guardian create an account and register for events, in which case they will assume liability for you. Apologies for any inconvenience, and thank you for your understanding."
    )
    mail.send(msg)

def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password) and
        re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    )

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    form = UserLoginForm()
    try:
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            print(f"Attempting login with Email: {email}, Password: {password}")

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                print(f"Found user: {user.email}")
                login_user(user)
                flash('Login successful!', 'success')
                session['role'] = user.role

                print(f"User {email} logged in successfully.")
                return render_template('signin.html', form=form, first_name=user.first_name)
            
            else:
                flash('Invalid email or password. ', 'error')
                print(f"No user found with email: {email}")
                return render_template('signin.html', form=form)
    except Exception as e:
        print(f"Error during login: {e}")
        flash('An error occurred during login. Please try again later.', 'error')

    return render_template('signin.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegistrationForm()

    if form.validate_on_submit():
        # --- Data Collection ---
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        
        # New waiver fields
        address = request.form.get('address')
        dob = request.form.get('dob')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        signature_data = request.form.get('signature_data') # Get signature image data

         # --- Age Calculation & Validation ---
        try:
            today = date.today()
            birthdate = date.fromisoformat(dob)
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        except (ValueError, TypeError):
            flash('Please enter a valid date of birth.', 'error')
            return render_template('register.html', form=form)

        if age < 18:
            flash('Sorry, you must be 18 years or older to create an account.', 'error')
            send_underage_rejection_email(email) # Send the rejection email
            return render_template('register.html', form=form) # Stop and show the form again


        # --- Validation ---
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please log in.', 'error')
            # 👇 CHANGE THIS LINE
            return render_template('register.html', form=form)
        
        if not is_strong_password(form.password.data):
            flash('Password must be at least 8 characters long...', 'error')
            # 👇 AND CHANGE THIS LINE
            return render_template('register.html', form=form)

        if form.password.data != form.confirm_password.data:
            flash('Passwords do not match.', 'error')
            # 👇 ALSO CHANGE THIS LINE (if you have it)
            return render_template('register.html', form=form)
    

        #  Profile Image Handling ---
        profile_image_filename = 'default.png'  # Default image
        cropped_image_data = request.form.get('cropped_image_data')

        if cropped_image_data:
            try:
                # Handle the cropped image data if it exists
                header, encoded = cropped_image_data.split(",", 1)
                image_data = base64.b64decode(encoded)
                filename = f"{uuid.uuid4().hex}.png"
                upload_path = os.path.join(current_app.root_path, 'static', 'profile_images', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                with open(upload_path, 'wb') as f:
                    f.write(image_data)
                profile_image_filename = filename
            except Exception as e:
                flash('There was an error processing the cropped image.', 'error')
                print(f"Error saving cropped image: {e}")
        
        elif 'profileImage' in request.files:
            # Fallback to the original file if no crop data is sent
            image = request.files['profileImage']
            if image and image.filename:
                ext = os.path.splitext(image.filename)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                upload_path = os.path.join(current_app.root_path, 'static', 'profile_images', filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                image.save(upload_path)
                profile_image_filename = filename

        role = 'admin' if email == 'tester@gmail.com' else 'user'
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role
        )
        user.address=address
        user.profile_image = profile_image_filename or 'default.png' # Set the profile image here instead
        user.set_password(password)
        db.session.add(user)
        db.session.commit() # Commit here to get the user.id

        try:
            header, encoded = signature_data.split(",", 1)
            signature_image_data = base64.b64decode(encoded)
        except (ValueError, TypeError):
            flash('Invalid signature data. Please sign again.', 'error')
            return render_template('register.html', form=form)
        
        # --- Detailed PDF Waiver Generation 
        def generate_detailed_waiver(user_data, signature_image, path):
            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter  # Page dimensions

            # Helper to draw wrapped paragraphs
            def draw_paragraph(text_object, text_content, max_width):
                words = text_content.split()
                line = ''
                for word in words:
                    # Use the text object's internal font state to calculate width
                    if c.stringWidth(line + ' ' + word, text_object._fontname, text_object._fontsize) < max_width:
                        line += ' ' + word
                    else:
                        text_object.textLine(line.strip())
                        line = word
                text_object.textLine(line.strip())

            # --- PAGE 1 ---
            text = c.beginText(1 * inch, height - 1 * inch)
            text.setFont("Helvetica-Bold", 12)
            text.textLine("WAIVER, ASSUMPTION OF RISK,")
            text.textLine("RELEASE OF LIABILITY & INDEMNIFICATION AGREEMENT")
            text.textLine(" ")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("PLEASE READ THIS ENTIRE DOCUMENT CAREFULLY BEFORE SIGNING.")
            text.textLine("THIS IS A RELEASE OF LIABILITY AND WAIVER OF CERTAIN LEGAL RIGHTS.")
            text.textLine(" ")
            
            text.setFont("Helvetica", 9)
            text.setLeading(12)

            p1 = 'This Waiver, Assumption of Risk, Release of Liability & Indemnification Agreement (this "Agreement") is a binding agreement with Portland Public Volleyball LLC, an Oregon limited liability company (the "Company") required by the Company as a condition to participate in volleyball games, leagues or tournaments, volleyball instruction or coaching, or similar activities (the "Activities").'
            p2 = 'This Agreement must be signed by the person identified as the Participant below (the "Participant"), and if the Participant is not at least 18 years of age, this Agreement must also be signed by the Participant\'s parent or guardian. The Participant and the parent or guardian signing this Agreement are referred to below as the "Releasing Parties", or each individually, as a "Releasing Party".'
            p3 = "By signing this Agreement, each Releasing Party agrees that the waivers, releases, and other terms of this Agreement are binding on each Releasing Party, that the terms of this Agreement are a material condition on the Company's agreement to allow the Participant to engage in the Activities, and that the Company would not allow the Participant to participate in the Activities without the Releasing Parties' acceptance of the terms of this Agreement."
            p4 = "By signing this Agreement, each Releasing Party agrees that they have carefully read and understood this Agreement (including but not limited to the terms and conditions set forth in numbered sections 1 through 7 below). By signing below, each Releasing Party also agrees that this Agreement waives and releases certain legal rights that such Releasing Party would otherwise have, and that this Agreement is binding to the fullest extent permitted by law."

            draw_paragraph(text, p1, width - 2 * inch)
            text.textLine("")
            draw_paragraph(text, p2, width - 2 * inch)
            text.textLine("")
            draw_paragraph(text, p3, width - 2 * inch)
            text.textLine("")
            draw_paragraph(text, p4, width - 2 * inch)

            text.textLine("")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("1. Assumption of Risks.")
            text.setFont("Helvetica", 9)
            p5 = "Each Releasing Party acknowledges and understands that THE ACTIVITIES CAN BE HAZARDOUS AND INVOLVES THE RISK OF PROPERTY DAMAGE, PHYSICAL INJURY AND/OR DEATH. Each Releasing Party understands the dangers and risks of the Activities and assumes all risks and dangers that are related to or may result from the Activities, including but not limited to: falling, slipping, tripping, loss of balance, collisions, injuries, Participant or another acting in a negligent or reckless manner that may cause and/or contribute to injury to Participant or others, storms and other adverse weather conditions, slick or uneven surfaces, holes, rocks, trees, marked and unmarked obstacles or dangers, equipment failure, equipment malfunction, equipment damage, Participant's improper use of equipment, limited access to and/or delay of medical attention, Participant's health condition, injuries that may result from strenuous activity, fatigue, exhaustion, dehydration, hypothermia, and mental distress from any of the above. Each Releasing Party acknowledges and understands that the description of the risks listed in the paragraph above are illustrative examples only and are not a complete list of potential risks and that the Activities may also include risks and dangers which are inherent and/or which cannot be reasonably avoided."
            p6 = "By signing this Agreement, each Releasing Party recognizes that property loss, injury, serious injury and death are all possible while participating in the Activities. EACH RELEASING PARTY AFFIRMS THAT HE OR SHE RECOGNIZES THE RISKS AND DANGERS, UNDERSTANDS THE DANGEROUS NATURE OF THE ACTIVITIES, VOLUNTARILY CHOOSES TO PARTICIPATE IN SUCH ACTIVITIES, AND EXPRESSLY ASSUMES ALL RISKS AND DANGERS OF THE ACTIVITIES, WHETHER OR NOT DESCRIBED ABOVE, KNOWN OR UNKNOWN, INHERENT OR OTHERWISE."
            
            draw_paragraph(text, p5, width - 2 * inch)
            text.textLine("")
            draw_paragraph(text, p6, width - 2 * inch)
            c.drawText(text)
            c.showPage() # END PAGE 1

            # --- PAGE 2 ---
            text = c.beginText(1 * inch, height - 1 * inch)
            text.setFont("Helvetica", 9)
            text.setLeading(12)

            text.setFont("Helvetica-Bold", 9)
            text.textLine("2. Covenant not to Sue.")
            text.setFont("Helvetica", 9)
            p7 = "THE RELEASING PARTIES EACH HEREBY AGREE NOT TO SUE THE COMPANY, the owner of the property or facilities where the Activities takes place, or any of their affiliates, successors in interest, affiliated organizations and companies, insurance carriers, agents, employees, representatives, assignees, officers, directors, shareholders, managers, members, partners and other related parties (each a \"Released Party\") for any injury or loss to Participant, including death, which Participant may suffer, arising in whole or in part out of Participant's participation in the Activities and for any property damage (including but not limited to equipment damage)."
            draw_paragraph(text, p7, width - 2 * inch)
            
            text.textLine("")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("3. Release and Indemnity by Releasing Parties.")
            text.setFont("Helvetica", 9)
            p8 = "EACH RELEASING PARTY AGREES TO HOLD HARMLESS AND RELEASE EACH AND EVERY RELEASED PARTY FROM ANY AND ALL LIABILITY AND/OR CLAIMS FOR INJURY OR DEATH TO PERSONS OR DAMAGE TO PROPERTY ARISING FROM PARTICIPATION IN THE ACTIVITIES, INCLUDING, BUT NOT LIMITED TO, THOSE CLAIMS BASED ON ANY RELEASED PARTY'S ALLEGED OR ACTUAL NEGLIGENCE OR BREACH OF ANY CONTRACT AND/OR EXPRESS OR IMPLIED WARRANTY. By execution of this Agreement, each Released Party also AGREES TO DEFEND AND INDEMNIFY each Released Party from any and all claims of the Participant and/or a third party arising in whole or in part from Participant's participation in the Activities."
            draw_paragraph(text, p8, width - 2 * inch)
            
            # --- NEWLY ADDED SECTIONS ---
            text.textLine("")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("4. No Assurances Regarding Locations, Facilities, or Equipment.")
            text.setFont("Helvetica", 9)
            p9 = "Each Releasing Party acknowledges that the Releasing Parties are solely responsible for determining that the locations, facilities and equipment are suitable and safe to be used for the Activities and for inspecting such locations, facilities and equipment to identify risks. Neither the Company nor any of the Released Parties have made any investigation or provided any assurances that the locations, facilities or equipment are suitable or safe for use in the Activities and have no duty of care or similar duty that would impose any obligation to do so. The Participant assumes all responsibility for any equipment provided by the Company and accepts full responsibility for its care and for all loss or damage that may be caused by or to the equipment, except reasonable wear and tear, while in Participant's possession."
            draw_paragraph(text, p9, width - 2 * inch)

            text.textLine("")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("5. Abilities of Participant; Health Risks.")
            text.setFont("Helvetica", 9)
            p10 = "Each Releasing Party represents and warrants to the Released Parties that Participant has the physical ability and knowledge to safely engage in the Activities, and has made all appropriate inquiries of doctors or other medical professionals to confirm that Participant is healthy and capable of safely participating in the Activities without unacceptable health risks."
            draw_paragraph(text, p10, width - 2 * inch)
            
            # --- NEW SECTION ADDED ---
            text.textLine("")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("6. Indemnification for Actions of Minors.")
            text.setFont("Helvetica", 9)
            p11_new = "Participant agrees that Participant is solely responsible for ensuring that any children of Participant or other minors present at the Activity at the invitation of Participant (a \"Minor Invitee\") is properly supervised and behaves in a manner that is safe and does not present a danger to the Minor Invitee or others. By execution of this Agreement, Participant also AGREES TO DEFEND AND INDEMNIFY each Released Party from any and all claims based on the actions or behavior of any Minor Invitee of such Participant at the Activity or the associated locations, facilities or use of any equipment."
            draw_paragraph(text, p11_new, width - 2 * inch)

            # --- RENUMBERED ---
            text.textLine("")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("7. Miscellaneous.")
            text.setFont("Helvetica", 9)
            p12 = "If any part of this Agreement is deemed to be unenforceable, such term shall be modified to the minimum extent permitted or severed, and the remaining terms shall be an enforceable contract between the parties. It is the intent of Releasing Parties that this Agreement shall be binding upon the assignees, heirs, next of kin, executors and personal representatives of the Releasing Parties."
            draw_paragraph(text, p12, width - 2 * inch)
            
            # --- RENUMBERED ---
            text.textLine("")
            text.setFont("Helvetica-Bold", 9)
            text.textLine("8. Participant:")
            text.setFont("Helvetica", 9)
            text.textLine("Participant represents and warrants to the Releasing Parties that:")
            c.drawText(text)
            
            # The vertical offset (9.7) is increased to move the checkbox further down the page.
            box_x, box_y = 1.1 * inch, height - 9.7 * inch 
            c.rect(box_x, box_y, 10, 10)
            c.setFont("ZapfDingbats", 12)
            c.drawString(box_x + 1, box_y + 2, u'✔')
            c.setFont("Helvetica", 9)
            c.drawString(1.3 * inch, height - 9.68 * inch, "Participant is 18 years of age or older.")
            c.showPage() # END PAGE 2

            # --- PAGE 3: SIGNATURE PAGE ---
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1 * inch, height - 1.5 * inch, "SIGNATURE OF PARTICIPANT")
            
            text = c.beginText(1 * inch, height - 1.8 * inch)
            text.setFont("Helvetica", 9)
            text.setLeading(12)
            p12 = "By signing below, the Participant agrees to each of the terms of this Agreement and acknowledges that the Participant would not be permitted to participate in the Activities except on the terms set forth in this Agreement."
            draw_paragraph(text, p12, width - 2 * inch)
            c.drawText(text)

            image_reader = io.BytesIO(signature_image)
            c.drawImage(ImageReader(image_reader), 1 * inch, height - 3.5 * inch, width=150, height=50, mask='auto')

            text = c.beginText(1 * inch, height - 4 * inch)
            text.setFont("Helvetica", 11)
            text.setLeading(16)
            text.textLine("_____________________________")
            text.textLine(f"Participant Name: {user_data['name']}")
            text.textLine(f"Date: {datetime.now().strftime('%B %d, %Y')}")
            text.textLine(f"Mailing Address: {user_data['address']}")
            text.textLine(f"Date of Birth: {user_data['dob']}")
            text.textLine("")
            text.textLine(f"Emergency Contact Name: {user_data['emergency_name']}")
            text.textLine(f"Emergency Contact Phone Number: {user_data['emergency_phone']}")
            c.drawText(text)
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1*inch, height - 7 * inch, "SIGNATURE OF PARENT OR LEGAL GUARDIAN")
            c.drawString(1*inch, height - 7.2 * inch, "(Required if Participant is not 18 years old or older)")
            c.save()

        waiver_filename = f"waiver_{user.id}.pdf"
        waiver_path = os.path.join(current_app.root_path, 'static', 'waivers', waiver_filename)
        os.makedirs(os.path.dirname(waiver_path), exist_ok=True)
        
        waiver_data_dict = { "name": f"{first_name} {last_name}", "address": address, "dob": dob, "emergency_name": emergency_contact_name, "emergency_phone": emergency_contact_phone }
        
        generate_detailed_waiver(waiver_data_dict, signature_image_data, waiver_path)

        # ... (your existing email logic) ...
        with open(waiver_path, 'rb') as f:
            pdf_bytes = f.read()
        
        def send_waiver_email(user_email, admin_email, pdf_data, user_name):
            msg = Message(
                subject=f"Waiver Confirmation for {user_name}",
                sender="noreply.pickupvbpdx@gmail.com",  # This explicit line overrides any incorrect defaults
                recipients=[user_email, admin_email],
                body=f"Attached is {user_name}'s signed waiver, assumption of risk, release of liability & Indemnification agreement for participation in events offered by Pick Up Volleyball PDX. "
            )
            msg.attach(f"waiver_{user.id}.pdf", "application/pdf", pdf_data)
            mail.send(msg)
        
        send_waiver_email(user.email, "noreply.pickupvbpdx@gmail.com", pdf_bytes, user.first_name)
        
        # --- Final Steps ---
        login_user(user)
        session['role'] = role
        flash('Account created successfully and you are now logged in!', 'success')
        return render_template('register.html', form=form, first_name=user.first_name)

    return render_template('register.html', form=form)

@auth.route('/signout', methods=['POST'])
@login_required
def signout():
    logout_user()
    session.pop('role', None)  # ✅ Ensure role is removed
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from app.forms import ProfileUpdateForm
    form = ProfileUpdateForm(obj=current_user)

    if request.method == 'POST':
        if 'update_details_submit' in request.form:
            # Check for new cropped image data first
            cropped_image_data = request.form.get('cropped_image_data')

            if cropped_image_data:
                try:
                    # Strip the header and decode the base64 string
                    header, encoded = cropped_image_data.split(",", 1)
                    image_data = base64.b64decode(encoded)

                    # Create a unique filename
                    filename = f"{uuid.uuid4().hex}.png"
                    upload_path = os.path.join(current_app.root_path, 'static', 'profile_images', filename)
                    
                    # Save the decoded data as a file
                    with open(upload_path, 'wb') as f:
                        f.write(image_data)

                    current_user.profile_image = filename
                    flash('Profile image updated successfully!', 'success')

                except Exception as e:
                    flash('There was an error processing the cropped image.', 'error')
                    print(f"Error saving cropped image: {e}")

            db.session.commit()
            return redirect(url_for('auth.profile'))

        # Check if the "Save New Password" button was clicked
        elif 'change_password_submit' in request.form:
            # Only process if the new_password field has data
            if form.new_password.data:
                # Check if the new passwords match
                if form.new_password.data == form.confirm_password.data:
                    # Check for password strength
                    if is_strong_password(form.new_password.data):
                        current_user.set_password(form.new_password.data)
                        db.session.commit()
                        flash('Password updated successfully!', 'success')
                    else:
                        flash('New password does not meet complexity requirements.', 'error')
                else:
                    flash('New passwords do not match.', 'error')
            else:
                flash('Please enter a new password.', 'error')
            return redirect(url_for('auth.profile'))
        
    # Fetch all active subscriptions for the current user
    active_subscriptions = Subscription.query.filter(
        Subscription.user_id == current_user.id,
        Subscription.status == 'active',
        Subscription.expiry_date >= date.today()
    ).all()

    # For a GET request, pre-populate the (disabled) name fields
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    today = date.today()

    return render_template('profile.html', form=form, today=today, active_subscriptions=active_subscriptions)


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            msg = Message(subject="Reset Your Password",
                          sender="noreply.pickupvbpdx@gmail.com",
                          recipients=[email],
                          body=f'Click the link to reset your password: {reset_url}')
            mail.send(msg)
            flash('If your email exists in our system, a password reset link has been sent. Please check your inbox.', 'success')
        else:
            flash('No account with that email.', 'error')
        return redirect(url_for('auth.forgot_password'))
    return render_template('forgot_password.html')


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception as e:
        flash('The password reset link is invalid or expired.', 'error')
        return redirect(url_for('auth.signin'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        if user:
            new_password = request.form['password']
            if not is_strong_password(new_password):
                flash('Password must meet complexity requirements.', 'error')
                return render_template('reset_password.html', token=token)
            user.set_password(new_password)
            db.session.commit()
            flash('Your password has been reset. Please log in.', 'success')
            return redirect(url_for('auth.signin'))
    return render_template('reset_password.html', token=token)

import os
from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from functools import wraps
from models import db, Admin, Doctor, Patient, Department, Appointment, Treatment, DoctorAvailability
from forms import (RegistrationForm, LoginForm, AddDoctorForm, TreatmentForm,
                   BookAppointmentForm, AvailabilityForm)
from datetime import datetime, date, time, timedelta


def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role_name:
                flash(f'This page is for {role_name}s only.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

admin_required = role_required('admin')
doctor_required = role_required('doctor')
patient_required = role_required('patient')

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config['SECRET_KEY'] = 'a-very-secret-key-that-is-long-and-secure'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        role = session.get('role')
        user_id = int(user_id)
        if role == 'admin': return Admin.query.get(user_id)
        elif role == 'doctor': return Doctor.query.get(user_id)
        elif role == 'patient': return Patient.query.get(user_id)
        return None

    with app.app_context():
        db.create_all()
        # Seed initial data if tables are empty
        if not Admin.query.filter_by(username='admin').first():
            admin_user = Admin(username='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
        if Department.query.count() == 0:
            departments = ['Cardiology', 'Neurology', 'Oncology', 'Pediatrics', 'Orthopedics', 'Dermatology']
            for dept_name in departments:
                db.session.add(Department(name=dept_name))
        db.session.commit()

  
    @app.route('/')
    def index():
        return render_template('index.html')

  
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated: return redirect(url_for('index'))
        form = RegistrationForm()
        if form.validate_on_submit():
            patient = Patient(name=form.name.data, email=form.email.data, phone=form.phone.data)
            patient.set_password(form.password.data)
            db.session.add(patient)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated: return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = None
            role = None
            admin = Admin.query.filter_by(username=form.email.data).first()
            if admin and admin.check_password(form.password.data):
                user, role, redirect_url = admin, 'admin', url_for('admin_dashboard')
            else:
                doctor = Doctor.query.filter_by(email=form.email.data).first()
                if doctor and doctor.check_password(form.password.data):
                    user, role, redirect_url = doctor, 'doctor', url_for('doctor_dashboard')
                else:
                    patient = Patient.query.filter_by(email=form.email.data).first()
                    if patient and patient.check_password(form.password.data):
                        user, role, redirect_url = patient, 'patient', url_for('patient_dashboard')

            if user:
                login_user(user)
                session['role'] = role
                return redirect(redirect_url)
            else:
                flash('Login Unsuccessful. Please check email and password.', 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    def logout():
        logout_user()
        session.pop('role', None)
        return redirect(url_for('index'))

    # ======================== ADMIN ROUTES ========================
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        stats = {
            'doctors': Doctor.query.count(),
            'patients': Patient.query.count(),
            'appointments': Appointment.query.count()
        }
        return render_template('admin/admin_dashboard.html', stats=stats)

    @app.route('/admin/add_doctor', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def add_doctor():
        form = AddDoctorForm()
        if form.validate_on_submit():
            doctor = Doctor(name=form.name.data, email=form.email.data, phone=form.phone.data, department=form.specialization.data)
            doctor.set_password(form.password.data)
            db.session.add(doctor)
            db.session.commit()
            flash('Doctor has been added successfully!', 'success')
            return redirect(url_for('view_doctors'))
        return render_template('admin/add_doctor.html', form=form)

    @app.route('/admin/view_doctors')
    @login_required
    @admin_required
    def view_doctors():
        query = request.args.get('query', '')
        q_filter = Doctor.name.contains(query) | Department.name.contains(query) if query else True
        doctors = Doctor.query.join(Department).filter(q_filter).all()
        return render_template('admin/view_doctors.html', doctors=doctors, query=query)
 
    @app.route('/admin/view_patients')
    @login_required
    @admin_required
    def view_patients():
        query = request.args.get('query', '')
        q_filter = Patient.name.contains(query) | Patient.id.like(f'%{query}%') | Patient.phone.contains(query) if query else True
        patients = Patient.query.filter(q_filter).all()
        return render_template('admin/view_patients.html', patients=patients, query=query)

    @app.route('/admin/view_appointments')
    @login_required
    @admin_required
    def view_appointments():
        appointments = Appointment.query.order_by(Appointment.appointment_datetime.desc()).all()
        return render_template('admin/view_appointments.html', appointments=appointments)

    @app.route('/admin/remove/<user_type>/<int:user_id>', methods=['POST'])
    @login_required
    @admin_required
    def remove_user(user_type, user_id):
        Model = Doctor if user_type == 'doctor' else Patient
        user = Model.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash(f'{user_type.title()} {user.name} has been removed.', 'success')
        return redirect(url_for(f'view_{user_type}s'))

    # ======================== DOCTOR ROUTES ========================
    @app.route('/doctor/dashboard')
    @login_required
    @doctor_required
    def doctor_dashboard():
        today = date.today()
        appointments = Appointment.query.filter_by(doctor_id=current_user.id)\
            .filter(db.func.date(Appointment.appointment_datetime) == today)\
            .order_by(Appointment.appointment_datetime).all()
        return render_template('doctor/doctor_dashboard.html', appointments=appointments)

    @app.route('/doctor/appointment/<int:appointment_id>/update_status', methods=['POST'])
    @login_required
    @doctor_required
    def update_appointment_status(appointment_id):
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id != current_user.id:
            flash('You do not have permission to modify this appointment.', 'danger')
            return redirect(url_for('doctor_dashboard'))
        appointment.status = request.form.get('status')
        db.session.commit()
        flash(f'Appointment status updated to {appointment.status}.', 'success')
        return redirect(url_for('doctor_dashboard'))

    @app.route('/doctor/appointment/<int:appointment_id>/add_treatment', methods=['GET', 'POST'])
    @login_required
    @doctor_required
    def add_treatment(appointment_id):
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id != current_user.id:
            return redirect(url_for('doctor_dashboard'))
        form = TreatmentForm()
        if form.validate_on_submit():
            treatment = Treatment(appointment_id=appointment.id, diagnosis=form.diagnosis.data, prescription=form.prescription.data)
            db.session.add(treatment)
            appointment.status = 'Completed'
            db.session.commit()
            flash('Treatment details added successfully.', 'success')
            return redirect(url_for('doctor_dashboard'))
        return render_template('doctor/add_treatment.html', form=form, appointment=appointment)

    @app.route('/doctor/patient_history/<int:patient_id>')
    @login_required
    @doctor_required
    def view_patient_history(patient_id):
        patient = Patient.query.get_or_404(patient_id)
        appointments = Appointment.query.filter_by(patient_id=patient.id, doctor_id=current_user.id)\
            .order_by(Appointment.appointment_datetime.desc()).all()
        return render_template('doctor/view_patient_history.html', patient=patient, appointments=appointments)

    @app.route('/doctor/availability', methods=['GET', 'POST'])
    @login_required
    @doctor_required
    def manage_availability():
        form = AvailabilityForm()
        if form.validate_on_submit():
            availability = DoctorAvailability.query.filter_by(doctor_id=current_user.id, day_of_week=form.day.data).first()
            if not availability:
                availability = DoctorAvailability(doctor_id=current_user.id, day_of_week=form.day.data)
            availability.start_time = form.start_time.data
            availability.end_time = form.end_time.data
            db.session.add(availability)
            db.session.commit()
            flash(f'Availability for {form.day.data} updated.', 'success')
            return redirect(url_for('manage_availability'))

        availabilities = DoctorAvailability.query.filter_by(doctor_id=current_user.id).all()
        return render_template('doctor/manage_availability.html', form=form, availabilities=availabilities)

    # ======================== PATIENT ROUTES ========================
    @app.route('/patient/dashboard')
    @login_required
    @patient_required
    def patient_dashboard():
        upcoming_appointments = Appointment.query.filter(Appointment.patient_id == current_user.id, Appointment.appointment_datetime >= datetime.now()).order_by(Appointment.appointment_datetime).all()
        return render_template('patient/patient_dashboard.html', appointments=upcoming_appointments)

    @app.route('/patient/book_appointment', methods=['GET', 'POST'])
    @login_required
    @patient_required
    def book_appointment():
        form = BookAppointmentForm()
        if request.method == 'POST':
            # Manually set choices for validation
            # ***FIXED HERE***
            form.doctor.choices = [(d.id, d.name) for d in Doctor.query.filter_by(specialization_id=form.department.data.id).all()]
            form.appointment_time.choices = [t for t in get_available_slots(form.doctor.data, form.appointment_date.data)]

            if form.validate_on_submit():
                doctor_id = int(form.doctor.data)
                date = form.appointment_date.data
                time_str = form.appointment_time.data
                hour, minute = map(int, time_str.split(':'))
                appointment_datetime = datetime.combine(date, time(hour, minute))

                # Final check for conflict prevention
                existing_appointment = Appointment.query.filter_by(doctor_id=doctor_id, appointment_datetime=appointment_datetime).first()
                if existing_appointment:
                    flash('This time slot has just been booked. Please select another time.', 'danger')
                    return redirect(url_for('book_appointment'))

                appointment = Appointment(patient_id=current_user.id, doctor_id=doctor_id, appointment_datetime=appointment_datetime, status='Booked')
                db.session.add(appointment)
                db.session.commit()
                flash('Appointment booked successfully!', 'success')
                return redirect(url_for('patient_dashboard'))
        return render_template('patient/book_appointment.html', form=form)

    @app.route('/patient/appointment/cancel/<int:appointment_id>', methods=['POST'])
    @login_required
    @patient_required
    def cancel_appointment(appointment_id):
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.patient_id != current_user.id:
            return redirect(url_for('patient_dashboard'))
        appointment.status = 'Cancelled'
        db.session.commit()
        flash('Appointment cancelled.', 'info')
        return redirect(url_for('patient_dashboard'))

    @app.route('/patient/history')
    @login_required
    @patient_required
    def view_history():
        appointments = Appointment.query.filter_by(patient_id=current_user.id)\
            .order_by(Appointment.appointment_datetime.desc()).all()
        return render_template('patient/view_history.html', appointments=appointments)

    # ======================== API & DYNAMIC CONTENT ROUTES ========================
    @app.route('/api/doctors_by_department/<int:dept_id>')
    def doctors_by_department(dept_id):
        # ***FIXED HERE***
        doctors = Doctor.query.filter_by(specialization_id=dept_id).all()
        return jsonify([{'id': d.id, 'name': d.name} for d in doctors])

    @app.route('/api/available_slots/<int:doctor_id>/<string:date_str>')
    def available_slots(doctor_id, date_str):
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        slots = get_available_slots(doctor_id, selected_date)
        return jsonify(slots)

    @app.route('/api/chart_data/admin')
    @login_required
    @admin_required
    def admin_chart_data():
        data = {
            "labels": ["Doctors", "Patients", "Appointments"],
            "datasets": [{
                "label": "Total Counts",
                "data": [Doctor.query.count(), Patient.query.count(), Appointment.query.count()],
                "backgroundColor": ["#0d6efd", "#198754", "#0dcaf0"]
            }]
        }
        return jsonify(data)

    # Helper function to get available time slots for a doctor on a specific date
    def get_available_slots(doctor_id, selected_date):
        day_name = selected_date.strftime('%A')
        availability = DoctorAvailability.query.filter_by(doctor_id=doctor_id, day_of_week=day_name).first()
        if not availability: return []

        booked_slots = [a.appointment_datetime.time() for a in Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            db.func.date(Appointment.appointment_datetime) == selected_date,
            Appointment.status != 'Cancelled'
        ).all()]

        available_slots = []
        current_time = datetime.combine(selected_date, availability.start_time)
        end_time = datetime.combine(selected_date, availability.end_time)

        while current_time < end_time:
            if current_time.time() not in booked_slots:
                if datetime.combine(selected_date, current_time.time()) > datetime.now(): # Check if slot is in the future
                    available_slots.append(current_time.strftime('%H:%M'))
            current_time += timedelta(minutes=30) # Assuming 30-minute slots

        return available_slots

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
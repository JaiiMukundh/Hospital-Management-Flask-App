from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField, TimeField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms_sqlalchemy.fields import QuerySelectField
from models import Patient, Department, Doctor
from datetime import date

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = Patient.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

def department_query():
    return Department.query

class AddDoctorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    specialization = QuerySelectField('Specialization', query_factory=department_query, get_label='name', allow_blank=False)
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Add Doctor')

    def validate_email(self, email):
        user = Doctor.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already in use by another doctor.')

class TreatmentForm(FlaskForm):
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    prescription = TextAreaField('Prescription', validators=[DataRequired()])
    submit = SubmitField('Submit Treatment')

class BookAppointmentForm(FlaskForm):
    department = QuerySelectField('Select Department', query_factory=department_query, get_label='name', allow_blank=True, validators=[DataRequired()])
    doctor = SelectField('Select Doctor', choices=[], validators=[DataRequired(message="Please select a department first to see available doctors.")])
    appointment_date = DateField('Select Date', validators=[DataRequired()], format='%Y-%m-%d')
    appointment_time = SelectField('Select Time', choices=[], validators=[DataRequired(message="Please select a date to see available times.")])
    submit = SubmitField('Book Appointment')

    def validate_appointment_date(self, appointment_date):
        if appointment_date.data < date.today():
            raise ValidationError("You cannot book an appointment in the past.")

class AvailabilityForm(FlaskForm):
    day = SelectField('Day of the Week', choices=[
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')
    ], validators=[DataRequired()])
    start_time = TimeField('Start Time', format='%H:%M', validators=[DataRequired()])
    end_time = TimeField('End Time', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Update Availability')
from django import forms
from django.contrib.auth.models import User

from . import models
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import datetime
from django.forms.widgets import SelectDateWidget
from django.utils import timezone

from .models import Admin, Student, Counsellor, Appointment, ApprovedStudentAppointment

service_field = \
    [('Counselling', 'Counselling'),
     ('Psychology', 'Psychology'),
     ('Therapy', 'Therapy'),
     ('Mentorship', 'Mentorship')]  # field for counsellors


# Admin registration form
class AdminRegistrationForm(UserCreationForm):  # to register an admin
    username = forms.CharField(required=True, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your username'}))
    username.widget.attrs.update({'class': 'app-form-control'})

    email = forms.EmailField(required=True, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your email'}))
    email.widget.attrs.update({'class': 'app-form-control'})

    first_name = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}))
    first_name.widget.attrs.update({'class': 'app-form-control'})

    last_name = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'}))
    last_name.widget.attrs.update({'class': 'app-form-control'})

    dob = forms.DateField(label="", widget=SelectDateWidget(years=range(1960, 2021)))
    dob.widget.attrs.update({'class': 'app-form-control-date'})

    address = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your address'}))
    address.widget.attrs.update({'class': 'app-form-control'})

    city = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'City'}))
    city.widget.attrs.update({'class': 'app-form-control'})

    country = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Country'}))
    country.widget.attrs.update({'class': 'app-form-control'})

    postcode = forms.IntegerField(label="", widget=forms.TextInput(attrs={'placeholder': 'Postcode'}))
    postcode.widget.attrs.update({'class': 'app-form-control'})

    image = forms.ImageField(label="")
    image.widget.attrs.update({'class': 'app-form-control'})

    password1 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password1.widget.attrs.update({'class': 'app-form-control'})

    password2 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password again'}))
    password2.widget.attrs.update({'class': 'app-form-control'})

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'dob', 'address', 'city', 'country', 'postcode',
                  'image', 'password1', 'password2']
        help_texts = {k: "" for k in fields}


# Admin details update form
class AdminUpdateForm(forms.ModelForm):  # used to edit an admin instance
    first_name = forms.CharField()
    last_name = forms.CharField()
    dob = forms.DateField(widget=SelectDateWidget(years=range(1960, 2022)))
    address = forms.CharField()
    city = forms.CharField()
    country = forms.CharField()
    postcode = forms.IntegerField()
    image = forms.ImageField(widget=forms.FileInput)

    class Meta:
        model = Admin
        fields = ['first_name', 'last_name', 'dob', 'address', 'city', 'country', 'postcode', 'image']


# Admin appointment form
class AdminAppointmentForm(forms.ModelForm):  # book an appointment by admin
    counsellor = forms.TypedChoiceField(label='')  # counsellor is chosen from existing counsellors in db
    counsellor.widget.attrs.update({'class': 'app-form-control'})
    student = forms.TypedChoiceField(label='')  # student is chosen from existing students in db
    student.widget.attrs.update({'class': 'app-form-control'})
    app_date = forms.DateField(label='', widget=SelectDateWidget(years=range(2022, 2024)))  # appointment date
    app_date.widget.attrs.update({'class': 'app-form-control-date'})
    app_time = forms.TypedChoiceField(label='')  # time of appointment
    app_time.widget.attrs.update({'class': 'app-form-control'})
    description = forms.CharField(max_length=300, label='',
                                  widget=forms.TextInput(attrs={'placeholder': 'Description'}))
    description.widget.attrs.update({'class': 'app-form-control'})

    def __init__(self, *args, **kwargs):
        super(AdminAppointmentForm, self).__init__(*args, **kwargs)
        self.fields['counsellor'].choices = [(c.id, c.first_name + " " + c.last_name + " (" + c.service_field + ")")
                                           for c in Counsellor.objects.filter(status=True).all()]
        # choose counsellors from db
        self.fields['student'].choices = [(c.id, c.first_name + " " + c.last_name + " (" + c.company_name + ")")
                                           for c in Student.objects.filter(status=True).all()]
        # choose students from db
        self.fields['app_time'].choices = [('9:00 AM', '9:00 AM'), ('10:00 AM', '10:00 AM'), ('11:00 AM', '11:00 AM'),
                                           ('13:00 PM', '13:00 PM'), ('14:00 PM', '14:00 PM'), ('15:00 PM', '15:00 PM'),
                                           ('16:00 PM', '16:00 PM'), ('17:00 PM', '17:00 PM')]
        # choices for time slot for appointment

    class Meta:
        model = Appointment
        fields = ['description', 'app_date', 'app_time']


# Student registration form
class StudentRegistrationForm(UserCreationForm):  # register student
    username = forms.CharField(required=True, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your username'}))
    username.widget.attrs.update({'class': 'app-form-control'})

    email = forms.EmailField(required=True, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your email'}))
    email.widget.attrs.update({'class': 'app-form-control'})

    first_name = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}))
    first_name.widget.attrs.update({'class': 'app-form-control'})

    last_name = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'}))
    last_name.widget.attrs.update({'class': 'app-form-control'})

    dob = forms.DateField(label="", widget=SelectDateWidget(years=range(1960, 2022)))
    dob.widget.attrs.update({'class': 'app-form-control-date'})

    course_name = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your course name'}))
    course_name.widget.attrs.update({'class': 'app-form-control'})

    student_address = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': '+254....'}))
    student_address.widget.attrs.update({'class': 'app-form-control'})

    image = forms.ImageField(label="")
    image.widget.attrs.update({'class': 'app-form-control'})

    password1 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password1.widget.attrs.update({'class': 'app-form-control'})

    password2 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password again'}))
    password2.widget.attrs.update({'class': 'app-form-control'})

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'dob', 'course_name', 'student_address',
                'image', 'password1', 'password2']
        help_texts = {k: "" for k in fields}


# Student update form
class StudentUpdateForm(forms.ModelForm):  # update student details
    first_name = forms.CharField()
    last_name = forms.CharField()
    dob = forms.DateField(widget=SelectDateWidget(years=range(1960, 2022)))
    course_name = forms.CharField()
    student_address = forms.CharField()
    image = forms.ImageField(widget=forms.FileInput)

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'dob', 'course_name', 'student_address', 'image']


# Student appointment form
class StudentAppointmentForm(forms.ModelForm):  # make an appointment by student
    counsellor = forms.TypedChoiceField(label='')  # choose counsellor from db
    counsellor.widget.attrs.update({'class': 'app-form-control'})
    # eng_id=forms.CharField(widget=forms.Select(choices=c))
    app_date = forms.DateField(label='', widget=SelectDateWidget(years=range(2022, 2024)))  # date of appointment
    app_date.widget.attrs.update({'class': 'app-form-control-date'})
    app_time = forms.TypedChoiceField(label='')  # time of appointment
    app_time.widget.attrs.update({'class': 'app-form-control'})
    description = forms.CharField(max_length=300, label='',
                                  widget=forms.TextInput(attrs={'placeholder': 'Description'}))
    description.widget.attrs.update({'class': 'app-form-control'})

    def __init__(self, *args, **kwargs):
        super(StudentAppointmentForm, self).__init__(*args, **kwargs)
        self.fields['counsellor'].choices = [(e.id, e.first_name + " " + e.last_name + " (" + e.service_field + ")")
                                           for e in Counsellor.objects.filter(status=True).all()]
        # choose counsellors from db
        self.fields['app_time'].choices = [('9:00:00', '9:00:00'), ('10:00:00', '10:00:00'), ('11:00:00', '11:00:00'),
                                           ('13:00:00', '13:00:00'), ('14:00:00', '14:00:00'), ('15:00 PM', '15:00:00'),
                                           ('16:00:00', '16:00:00'), ('17:00:00', '17:00:00')]
        # choices for time slot for appointment

    class Meta:
        model = Appointment
        fields = ['description', 'app_date', 'app_time']


# Counsellor registration form
class CounsellorRegistrationForm(UserCreationForm):  # register counsellor
    username = forms.CharField(required=True, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your username'}))
    username.widget.attrs.update({'class': 'app-form-control'})

    email = forms.EmailField(required=True, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your email'}))
    email.widget.attrs.update({'class': 'app-form-control'})

    first_name = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your first name'}))
    first_name.widget.attrs.update({'class': 'app-form-control'})

    last_name = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your last name'}))
    last_name.widget.attrs.update({'class': 'app-form-control'})

    dob = forms.DateField(label="", widget=SelectDateWidget(years=range(1960, 2021)))
    dob.widget.attrs.update({'class': 'app-form-control-date'})

    address = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your address'}))
    address.widget.attrs.update({'class': 'app-form-control'})

    city = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'City'}))
    city.widget.attrs.update({'class': 'app-form-control'})

    country = forms.CharField(label="", widget=forms.TextInput(attrs={'placeholder': 'Country'}))
    country.widget.attrs.update({'class': 'app-form-control'})

    postcode = forms.IntegerField(label="", widget=forms.TextInput(attrs={'placeholder': 'Postcode'}))
    postcode.widget.attrs.update({'class': 'app-form-control'})

    image = forms.ImageField(label="")
    image.widget.attrs.update({'class': 'app-form-control'})

    service_field = forms.CharField(label="", widget=forms.Select(choices=service_field))
    service_field.widget.attrs.update({'class': 'app-form-control'})

    password1 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password1.widget.attrs.update({'class': 'app-form-control'})

    password2 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password again'}))
    password2.widget.attrs.update({'class': 'app-form-control'})

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'service_field', 'dob', 'address', 'city', 'country',
                  'postcode', 'image', 'password1', 'password2']
        help_texts = {k: "" for k in fields}

    def check_date(self):  # form date of birth validator
        cleaned_data = self.cleaned_data
        dob = cleaned_data.get('dob')
        if dob < timezone.now().date():
            return True
        self.add_error('dob', 'Invalid date of birth.')
        return False


# Counsellor update details form
class CounsellorUpdateForm(forms.ModelForm):  # update counsellor details
    first_name = forms.CharField()
    last_name = forms.CharField()
    # age = forms.IntegerField()
    dob = forms.DateField(widget=SelectDateWidget(years=range(1960, 2022)))
    address = forms.CharField()
    city = forms.CharField()
    country = forms.CharField()
    postcode = forms.IntegerField()
    image = forms.ImageField(widget=forms.FileInput)

    # appfees = forms.FloatField()
    # admfees = forms.FloatField()

    class Meta:
        model = Counsellor
        fields = ['first_name', 'last_name', 'dob', 'address', 'city', 'country', 'postcode', 'image']
        # 'appfees', 'admfees']


# Counsellor approve appointment form
class AppointmentApprovalForm(forms.ModelForm):  # counsellor approves an appointment
    description = forms.CharField(max_length=300, label='',
                                  widget=forms.TextInput(attrs={'placeholder': 'DESCRIPTION'}))
    description.widget.attrs.update({'class': 'app-form-control'})
    approval_date = forms.DateField(label='', widget=SelectDateWidget)
    approval_date.widget.attrs.update({'class': 'app-form-control-date'})

    class Meta:
        model = ApprovedStudentAppointment
        fields = ['description', 'approval_date']


# Counsellor edit appointment form
class AppointmentUpdateForm(forms.ModelForm):
    # counsellor can edit appointment description field, be it adding new lines or deleting a few of the old one
    description = forms.CharField(max_length=300, label='',
                                  widget=forms.TextInput(attrs={'placeholder': 'DESCRIPTION'}))
    description.widget.attrs.update({'class': 'app-form-control'})

    class Meta:
        model = Appointment
        fields = ['description']


# Feedback form
class FeedbackForm(forms.Form):  # contact us form (feedback), used by students/counsellors to send feedbacks using mail to admins
    APPOINTMENT = 'app'
    BUG = 'b'
    FEEDBACK = 'fb'
    NEW_FEATURE = 'nf'
    OTHER = 'o'
    subject_choices = (
        (APPOINTMENT, 'Appointment'),
        (FEEDBACK, 'Feedback'),
        (NEW_FEATURE, 'Feature Request'),
        (BUG, 'Bug'),
        (OTHER, 'Other'),
    )

    Name = forms.CharField(max_length=30, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your name'}))
    Name.widget.attrs.update({'class': 'form-control'})
    Email = forms.EmailField(label="", widget=forms.TextInput(attrs={'placeholder': 'example@email.com'}))
    Email.widget.attrs.update({'class': 'form-control'})
    Subject = forms.ChoiceField(label='', choices=subject_choices)
    Subject.widget.attrs.update({'class': 'form-control'})
    Message = forms.CharField(max_length=500, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter your message here'}))
    Message.widget.attrs.update({'class': 'form-control'})

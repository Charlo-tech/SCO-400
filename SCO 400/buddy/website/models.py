from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
import datetime

service_field = \
    [('Counselling', 'Counselling'),
     ('Psychology', 'Psychology'),
     ('Therapy', 'Therapy'),
     ('Mentorship', 'Mentorship')]  # field for counsellors


# Default user - deleted
def default_user():  # deleted users
    user = User(username="deleteduser", email="deleteduser@deleted.com")
    return user.id


# Admin
class Admin(models.Model):  # Admin details
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Admin")  # user foreign key
    image = models.ImageField(default="default.png", upload_to="profile_pictures")  # profile picture
    first_name = models.CharField(max_length=100, default='first_name')  # admin first name
    last_name = models.CharField(max_length=100, default='last_name')  # admin lastname
    dob = models.DateField(default=datetime.date.today)  # date of birth
    # contact?
    address = models.CharField(max_length=300, default="address")  # admin address
    city = models.CharField(max_length=100, default="city")  # admin city
    country = models.CharField(max_length=100, default="country")  # admin country
    postcode = models.IntegerField(default=0)  # admin postcode
    status = models.BooleanField(default=False)  # admin status (approved/on-hold)

    def __str__(self):
        return f'{self.admin.username} Admin Profile'


# Student
class Student(models.Model):  # Student details
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Student")  # user foreign key
    image = models.ImageField(default="default.png", upload_to="profile_pictures", null=True,
                              blank=True)  # profile picture
    first_name = models.CharField(max_length=100, default='first_name')  # student first name
    last_name = models.CharField(max_length=100, default='last_name')  # student last name
    dob = models.DateField(default=datetime.date.today)  # student date of birth
    course_name = models.CharField(max_length=300, default="course_name")  # student address
    student_address = models.CharField(max_length=300, default="student_address")  # student address
    # contact?
    status = models.BooleanField(default=False)  # student status (approved/on-hold)

    def __str__(self):
        return f'{self.student.username} Student Profile'


# Counsellor
class Counsellor(models.Model):  # counsellor details
    counsellor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Counsellor")  # user foreign key
    image = models.ImageField(default="default.png", upload_to="profile_pictures")  # profile picture
    first_name = models.CharField(max_length=100, default='first_name')  # counsellor firstname
    last_name = models.CharField(max_length=100, default='last_name')  # counsellor lastname
    dob = models.DateField(default=datetime.date.today)  # counsellor date of birth
    address = models.CharField(max_length=300, default="address")  # counsellor address
    city = models.CharField(max_length=100, default="city")  # counsellor city
    country = models.CharField(max_length=100, default="country")  # counsellor country
    postcode = models.IntegerField(default=0)  # counsellor postcode
    service_field = models.CharField(max_length=50, choices=service_field,
                                     default='Counsellor')  # counsellor service field from choices given as list
    status = models.BooleanField(default=False)  # counsellor status(approved/on-hold)

    def __str__(self):
        return f'{self.counsellor.username} Counsellor Profile'


# Counsellor service field
class CounsellorServiceField(models.Model):
    counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE, related_name="CounsellorServiceField")  # counsellor fk
    app_total = models.IntegerField(default=0)  # total students/appointments completed by counsellor

    def __str__(self):
        return f'{self.counsellor.first_name} Service Field Information'


# Appointment
class Appointment(models.Model):  # student appointment details
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="StudentApp")  # student fk
    counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE, related_name="CounsellorApp")  # counsellor fk
    description = models.TextField(max_length=500)  # appointment description
    app_link = models.TextField(null=True, blank=True)  # video call room link
    app_date = models.DateField(null=True, blank=True)  # call date
    app_time = models.TimeField(null=True, blank=True)  # call time/slot
    status = models.BooleanField(default=False)  # appointment status (approved/on-hold)
    completed = models.BooleanField(default=False)  # appointment completed/to-be-done
    # approval_date = models.DateField(null=True, blank=True)  # date appointment approved
    rating = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.description} Appointment Information'


# Appointment rating
class AppointmentRating(models.Model):
    rating = models.IntegerField(default=0,
                                 validators=[
                                     MaxValueValidator(5),
                                     MinValueValidator(0)])

    def __str__(self):
        return f'{self.rating} Stars - Appointment Rating Information'


# Approved appointment
class ApprovedStudentAppointment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="StudentApprovedApp")  # student fk
    counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE, related_name="CounsellorApprovedApp")  # counsellor fk
    approval_date = models.DateField()  # date appointment approved
    description = models.TextField()  # appointment description
    completed_date = models.DateField(null=True, blank=True)  # date of completed appointment

    def __str__(self):
        return f'{self.student} Approved Appointment Information'

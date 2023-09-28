""" from django.shortcuts import render

def home(request):
    return render(request, 'index.html') """
from django.conf import settings
from django.core import serializers
from django.core.mail import send_mail, mail_admins
from django.db.models.functions import TruncMonth

from . import forms, models

from datetime import date, time
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone

from django.shortcuts import render, redirect
from xhtml2pdf import pisa

from website.forms import AdminRegistrationForm, AdminUpdateForm, AdminAppointmentForm, StudentRegistrationForm, \
    StudentUpdateForm, StudentAppointmentForm, CounsellorRegistrationForm, CounsellorUpdateForm, AppointmentUpdateForm, \
    AppointmentApprovalForm
from website.models import Admin, Counsellor, Student, Appointment, CounsellorServiceField, \
    ApprovedStudentAppointment, AppointmentRating

import datetime


# Home
def home_view(request):  # Homepage
    return render(request, 'appointments/home/index.html')


# Account
def login_view(request):  # Login
    return render(request, 'appointments/account/login.html')


# Admin
def register_adm_view(request):  # register admin
    if request.method == "POST":
        registration_form = AdminRegistrationForm(request.POST, request.FILES)
        if registration_form.is_valid():  # get data from form (if it is valid)
            dob = registration_form.cleaned_data.get('dob')  # get date of birth from form
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))  # calculate age from dob
            if dob < timezone.now().date():  # check if date of birth is valid (happened the previous day or even back)
                new_user = User.objects.create_user(username=registration_form.cleaned_data.get('username'),
                                                    email=registration_form.cleaned_data.get('email'),
                                                    password=registration_form.cleaned_data.get(
                                                        'password1'))  # create user
                adm = Admin(admin=new_user,
                            first_name=registration_form.cleaned_data.get('first_name'),
                            last_name=registration_form.cleaned_data.get('last_name'),
                            # age=form.cleaned_data.get('age'),
                            dob=registration_form.cleaned_data.get('dob'),
                            address=registration_form.cleaned_data.get('address'),
                            city=registration_form.cleaned_data.get('city'),
                            country=registration_form.cleaned_data.get('country'),
                            postcode=registration_form.cleaned_data.get('postcode'),
                            image=request.FILES['image']
                            )  # create admin
                adm.save()
                group = Group.objects.get_or_create(name='Admin')  # add user to admin group
                group[0].user_set.add(new_user)

                messages.add_message(request, messages.INFO, 'Registration successful!')
                return redirect('login_adm.html')
            else:
                registration_form.add_error('dob', 'Invalid date of birth.')
        else:
            print(registration_form.errors)
            return render(request, 'appointments/admin/register_adm.html', {'registration_form': registration_form})
    else:
        registration_form = AdminRegistrationForm()

    return render(request, 'appointments/admin/register_adm.html', {'registration_form': registration_form})


# Login admin
def login_adm_view(request):  # login admin
    if request.method == "POST":
        login_form = AuthenticationForm(request=request, data=request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')  # get username
            password = login_form.cleaned_data.get('password')  # get password
            user = auth.authenticate(username=username, password=password)  # authenticate user
            if user is not None and check_admin(user):  # if user exists and is admin
                auth.login(request, user)  # login user
                account_approval = Admin.objects.all().filter(status=True,
                                                              admin_id=request.user.id)  # if account is approved
                if account_approval:
                    return redirect('profile_adm.html')
                    # return redirect('dashboard_adm.html')
                else:  # if account is not yet approved
                    auth.logout(request)
                    messages.add_message(request, messages.INFO, 'Your account is currently pending. '
                                                                 'Please wait for approval.')
                    return render(request, 'appointments/admin/login_adm.html', {'login_form': login_form})
        return render(request, 'appointments/admin/login_adm.html', {'login_form': login_form})
    else:
        login_form = AuthenticationForm()

    return render(request, 'appointments/admin/login_adm.html', {'login_form': login_form})


# Admin dashboard
@login_required(login_url='login_adm.html')
def dashboard_adm_view(request):
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        adm_det = Admin.objects.all().filter(status=False)
        eng = Counsellor.objects.all().filter(status=False)  # get all on-hold counsellors
        cust = Student.objects.all().filter(status=False)  # get all on-hold students
        app = Appointment.objects.all().filter(status=False)  # get all on-hold appointments

        adm_total = Admin.objects.all().count()  # total students
        cust_total = Student.objects.all().count()  # total students
        eng_total = Counsellor.objects.all().count()  # get total counsellors
        app_total = Appointment.objects.all().count()  # get total appointments

        pending_adm_total = Admin.objects.all().filter(status=False).count()  # count onhold admins
        pending_cust_total = Student.objects.all().filter(status=False).count()  # get total onhold students
        pending_eng_total = Counsellor.objects.all().filter(status=False).count()  # get total onhold counsellors
        pending_app_total = Appointment.objects.all().filter(status=False).count()  # get total onhold appointments

        messages.add_message(request, messages.INFO, 'There are {0} appointments that require approval.'.format(pending_app_total))

        context = {'adm': adm, 'eng': eng, 'cust': cust, 'app': app, 'adm_det': adm_det,
                   'adm_total': adm_total, 'cust_total': cust_total, 'eng_total': eng_total, 'app_total': app_total,
                   'pending_adm_total': pending_adm_total, 'pending_cust_total': pending_cust_total,
                   'pending_eng_total': pending_eng_total,
                   'pending_app_total': pending_app_total}  # render information

        return render(request, 'appointments/admin/dashboard_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Admin profile
@login_required(login_url='login_adm.html')
def profile_adm_view(request):
    if check_admin(request.user):
        # get information from database
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        dob = adm.dob
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if request.method == "POST":  # profile is updated
            admin_update_form = AdminUpdateForm(request.POST, request.FILES, instance=adm)
            if admin_update_form.is_valid():
                admin_update_form.save()  # save changes in profile

                messages.add_message(request, messages.INFO, 'Profile updated successfully!')
                return redirect('profile_adm.html')
        else:
            admin_update_form = AdminUpdateForm(instance=adm)
        context = {  # render information on webpage
            'admin_update_form': admin_update_form,
            'adm': adm,
            'age': age
        }
        return render(request, 'appointments/admin/profile_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Admin book appointment
@login_required(login_url='login_adm.html')
def book_app_adm_view(request):  # book appointment
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        if request.method == "POST":  # if form is submitted
            app_form = AdminAppointmentForm(request.POST)
            if app_form.is_valid():
                eng_id = app_form.cleaned_data.get('counsellor')  # get counsellor id
                cust_id = app_form.cleaned_data.get('student')  # get student id

                eng = Counsellor.objects.all().filter(id=eng_id).first()  # get counsellor
                cust = Student.objects.all().filter(id=cust_id).first()  # get student

                if check_eng_availability(eng, app_form.cleaned_data.get('app_date'),
                                          app_form.cleaned_data.get(
                                              'app_time')):  # check if appointment is available during that slot
                    app = Appointment(counsellor=eng, student=cust,
                                      description=app_form.cleaned_data.get('description'),
                                      app_date=app_form.cleaned_data.get('app_date'),
                                      app_time=app_form.cleaned_data.get('app_time'),
                                      status=True)  # create new appointment
                    app.save()
                    messages.add_message(request, messages.INFO, 'Appointment created.')
                    return redirect('book_app_adm.html')
                else:  # if slot is not available, display error
                    messages.add_message(request, messages.INFO, 'Time slot unavailable.')
                    return render(request, 'appointments/admin/book_app_adm.html', {'app_form': app_form})
            else:
                messages.add_message(request, messages.INFO, 'Error creating an appointment. Please try again.')
                print(app_form.errors)
        else:
            app_form = AdminAppointmentForm()
        return render(request, 'appointments/admin/book_app_adm.html',
                      {'adm': adm, 'app_form': app_form})
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Admin download summary report
def dl_report_adm_action(request):
    template_path = 'appointments/admin/summary_report.html'

    adm = Admin.objects.filter(admin_id=request.user.id).first()
    adm_det = Admin.objects.all().filter(status=False)
    eng = Counsellor.objects.all().filter(status=False)  # get all on-hold counsellors
    cust = Student.objects.all().filter(status=False)  # get all on-hold students
    app = Appointment.objects.all().filter(status=False)  # get all on-hold appointments

    adm_total = Admin.objects.all().count()  # total students
    cust_total = Student.objects.all().count()  # total students
    eng_total = Counsellor.objects.all().count()  # get total counsellors
    app_total = Appointment.objects.all().count()  # get total appointments

    pending_adm_total = Admin.objects.all().filter(status=False).count()  # count onhold admins
    pending_cust_total = Student.objects.all().filter(status=False).count()  # get total onhold students
    pending_eng_total = Counsellor.objects.all().filter(status=False).count()  # get total onhold counsellors
    pending_app_total = Appointment.objects.all().filter(status=False).count()  # get total onhold appointments

    context = {'adm': adm, 'eng': eng, 'cust': cust, 'app': app, 'adm_det': adm_det,
               'adm_total': adm_total, 'cust_total': cust_total, 'eng_total': eng_total, 'app_total': app_total,
               'pending_adm_total': pending_adm_total, 'pending_cust_total': pending_cust_total,
               'pending_eng_total': pending_eng_total,
               'pending_app_total': pending_app_total}

    # context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="buddy-summary-report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


# Admin approve appointment
@login_required(login_url='login_adm.html')
def approve_app_adm_action(request, pk):
    if check_admin(request.user):
        # get information from database
        appointment = Appointment.objects.get(id=pk)
        appointment.status = True  # approve appointment
        appointment.save()

        messages.success(request, "Appointment approved successfully.")
        return redirect(reverse('view_all_app_adm.html'))
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# All appointments: pending, incomplete, completed
@login_required(login_url='login_adm.html')
def all_app_adm_view(request):
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        app = Appointment.objects.all().filter(status=False)
        appointment_app = Appointment.objects.all().filter(status=False).count()
        app_count = Appointment.objects.all().count()
        pending_app_total = Appointment.objects.all().filter(status=False).count()
        approved_app_total = Appointment.objects.all().filter(status=True).count()

        appointment_details = []
        for app in Appointment.objects.filter(status=True).all():  # get approved appointments
            e = app.counsellor
            c = app.student
            if e and c:
                appointment_details.append([e.first_name, e.last_name, e.service_field,
                                            c.first_name, c.last_name, c.course_name,
                                            app.description, app.app_date, app.app_time,
                                            app.pk, app.completed, app.status])  # render information

        pending_appointment_details = []
        for app in Appointment.objects.filter(status=False).all():  # get pending appointments
            e = app.counsellor
            c = app.student
            if e and c:
                pending_appointment_details.append([e.first_name, e.last_name, e.service_field,
                                                    c.first_name, c.last_name, c.course_name,
                                                    app.description, app.app_date, app.app_time,
                                                    app.id, app.completed, app.status])  # render information on webpage

        return render(request, 'appointments/admin/view_all_app_adm.html',
                      {'adm': adm, 'app': app, 'appointment_app': appointment_app, 'app_count': app_count,
                       'pending_app_total': pending_app_total, 'approved_app_total': approved_app_total,
                       'appointment_details': appointment_details,
                       'pending_appointment_details': pending_appointment_details})
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Admin appointment view
@login_required(login_url='login_adm.html')
def appointment_adm_view(request):
    if check_admin(request.user):
        # get information from database and render in html webpage
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        app = Appointment.objects.all().filter(status=False)
        appointment_app = Appointment.objects.all().filter(status=False).count()
        app_count = Appointment.objects.all().count()
        pending_app_total = Appointment.objects.all().filter(status=False).count()
        approved_app_total = Appointment.objects.all().filter(status=True).count()
        context = {'adm': adm, 'app': app, 'appointment_app': appointment_app, 'app_count': app_count,
                   'pending_app_total': pending_app_total, 'approved_app_total': approved_app_total}
        return render(request, 'appointments/admin/appointment_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Approved appointment's details
@login_required(login_url='login_adm.html')
def app_details_adm_view(request, pk):
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()

        app = Appointment.objects.filter(id=pk).first()  # get appointment
        eng = app.counsellor
        cust = app.student

        app.app_link = cust.first_name

        appointment_details = [eng.first_name, eng.last_name, eng.service_field,
                               cust.first_name, cust.last_name,
                               cust.course_name, cust.student_address,
                               app.app_date, app.app_time, app.app_link, app.description,
                               app.status, app.completed, pk]  # render fields

        return render(request, 'appointments/admin/view_app_details_adm.html',
                      {'adm': adm,
                       'eng': eng,
                       'app': app,
                       'cust': cust,
                       'appointment_details': appointment_details})
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Complete appointment action
@login_required(login_url='login_adm.html')
def complete_app_adm_action(request, pk):
    if check_admin(request.user):
        # get information from database and render in html webpage
        app = Appointment.objects.get(id=pk)
        app.completed = True
        app.save()

        messages.add_message(request, messages.INFO, 'Appointment completed successfully!')
        return redirect('view_all_app_adm.html')
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Statistics page
@login_required(login_url='login_adm.html')
def statistics_adm_view(request):
    if check_admin(request.user):
        eng = Counsellor.objects.all().filter(status=False)  # get all on-hold counsellors
        cust = Student.objects.all().filter(status=False)  # get all on-hold students

        cust_total = Student.objects.all().count()  # total students
        eng_total = Counsellor.objects.all().count()  # get total counsellors
        app_total = Appointment.objects.all().count()  # get total appointments

        pending_cust_total = Student.objects.all().filter(status=False).count()  # get total onhold students
        pending_eng_total = Counsellor.objects.all().filter(status=False).count()  # get total onhold counsellors
        pending_app_total = Appointment.objects.all().filter(status=False).count()  # get total onhold appointments

        context = {'eng': eng, 'cust': cust,
                   'cust_total': cust_total, 'eng_total': eng_total, 'app_total': app_total,
                   'pending_cust_total': pending_cust_total, 'pending_eng_total': pending_eng_total,
                   'pending_app_total': pending_app_total}  # render information

        return render(request, 'appointments/admin/view_statistics_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# View statistics (pivot data)
@login_required(login_url='login_adm.html')
def pivot_data(request):
    dataset = Appointment.objects.all()
    data = serializers.serialize('json', dataset)
    return JsonResponse(data, safe=False)


# Student section
@login_required(login_url='login_adm.html')
def student_adm_view(request):
    if check_admin(request.user):
        # get information from database and render in html webpage
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        cust = Student.objects.all().filter(status=False)
        cust_approved = Student.objects.all().filter(status=True).count()
        cust_pending = Student.objects.all().filter(status=False).count()
        cust_count = Student.objects.all().count()
        context = {'adm': adm, 'cust': cust, 'cust_pending': cust_pending, 'cust_approved': cust_approved,
                   'cust_count': cust_count}
        return render(request, 'appointments/admin/student_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Approve student account
@login_required(login_url='login_adm.html')
def approve_cust_adm_view(request):  # Approve student
    # get information from database and render in html webpage
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        cust = Student.objects.all().filter(status=False)
        cust_approved = Student.objects.all().filter(status=True).count()
        cust_pending = Student.objects.all().filter(status=False).count()
        cust_count = Student.objects.all().count()

        context = {'adm': adm, 'cust': cust, 'cust_pending': cust_pending, 'cust_approved': cust_approved,
                   'cust_count': cust_count}

        return render(request, 'appointments/admin/approve_cust.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Approve student action
@login_required(login_url='login_adm.html')
def approve_cust_adm_action(request, pk):
    if check_admin(request.user):
        # get information from database
        cust = Student.objects.get(id=pk)
        cust.status = True  # approve student
        cust.save()

        messages.add_message(request, messages.INFO, 'Student approved successfully.')
        return redirect(reverse('approve_cust.html'))
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# View all students
@login_required(login_url='login_adm.html')
def all_cust_adm_view(request):  # View all students
    if check_admin(request.user):
        # get information from database and render in html webpage
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        cust = Student.objects.all().filter(status=False)
        cust_approved = Student.objects.all().filter(status=True).count()
        cust_pending = Student.objects.all().filter(status=False).count()
        cust_count = Student.objects.all().count()
        cust_details = []

        for c in Student.objects.filter(status=True).all():
            cust_details.append([c.id, c.image.url,
                                 c.first_name, c.last_name, c.dob,
                                 c.course_name, c.student_address,
                                 c.status])

        context = {'adm': adm, 'cust': cust, 'cust_pending': cust_pending, 'cust_approved': cust_approved,
                   'cust_count': cust_count, 'cust_details': cust_details}

        return render(request, 'appointments/admin/view_all_cust.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Counsellor section
@login_required(login_url='login_adm.html')
def counsellor_adm_view(request):  # view counsellors
    if check_admin(request.user):
        # get information from database and render in html webpage
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        eng = Counsellor.objects.all().filter(status=False)
        eng_approved = Counsellor.objects.all().filter(status=True).count()
        eng_pending = Counsellor.objects.all().filter(status=False).count()
        eng_count = Counsellor.objects.all().count()
        context = {'adm': adm, 'eng': eng, 'eng_approved': eng_approved, 'eng_pending': eng_pending,
                   'eng_count': eng_count}
        return render(request, 'appointments/admin/counsellor_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Approve counsellor account
@login_required(login_url='login_adm.html')
def approve_eng_adm_view(request):
    if check_admin(request.user):
        # get information from database and render in html webpage
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        eng = Counsellor.objects.all().filter(status=False)
        eng_approved = Counsellor.objects.all().filter(status=True).count()
        eng_pending = Counsellor.objects.all().filter(status=False).count()
        eng_count = Counsellor.objects.all().count()
        context = {'adm': adm, 'eng': eng, 'eng_approved': eng_approved, 'eng_pending': eng_pending,
                   'eng_count': eng_count}
        return render(request, 'appointments/admin/approve_eng.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Approve counsellor action
@login_required(login_url='login_adm.html')
def approve_eng_adm_action(request, pk):
    if check_admin(request.user):
        # get information from database
        eng = Counsellor.objects.get(id=pk)
        eng.status = True  # approve counsellor
        eng.save()

        messages.add_message(request, messages.INFO, 'Counsellor approved successfully.')
        return redirect(reverse('approve_eng.html'))
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# View all counsellors
@login_required(login_url='login_adm.html')
def all_eng_adm_view(request):
    # get information from database and render in html webpage
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        eng = Counsellor.objects.all().filter(status=False)
        eng_approved = Counsellor.objects.all().filter(status=True).count()
        eng_pending = Counsellor.objects.all().filter(status=False).count()
        eng_count = Counsellor.objects.all().count()

        eng_details = []
        for e in Counsellor.objects.filter(status=True).all():
            esf = CounsellorServiceField.objects.filter(counsellor=e).first()
            eng_details.append(
                [e.id, e.image.url, e.first_name, e.last_name, e.dob, e.address, e.postcode, e.city, e.country,
                 e.service_field, e.status, esf.app_total])

        context = {'adm': adm, 'eng': eng, 'eng_approved': eng_approved, 'eng_pending': eng_pending,
                   'eng_count': eng_count, 'eng_details': eng_details}

        return render(request, 'appointments/admin/view_all_eng.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# View admin
@login_required(login_url='login_adm.html')
def admin_adm_view(request):
    # get information from database and render in html webpage
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        adm_details = Admin.objects.all().filter()
        adm_approved = Admin.objects.all().filter(status=True).count()
        adm_pending = Admin.objects.all().filter(status=False).count()
        adm_count = Admin.objects.all().count()
        context = {'adm': adm,
                   'adm_details': adm_details,
                   'adm_approved': adm_approved,
                   'adm_pending': adm_pending,
                   'adm_count': adm_count}
        return render(request, 'appointments/admin/admin_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Approve admin account
@login_required(login_url='login_adm.html')
def approve_adm_adm_view(request):
    if check_admin(request.user):
        # get information from database and render in html webpage
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        adm_details = Admin.objects.all().filter(status=False)
        adm_approved = Admin.objects.all().filter(status=True).count()
        adm_pending = Admin.objects.all().filter(status=False).count()
        adm_count = Admin.objects.all().count()
        context = {'adm': adm,
                   'adm_details': adm_details,
                   'adm_approved': adm_approved,
                   'adm_pending': adm_pending,
                   'adm_count': adm_count}

        return render(request, 'appointments/admin/approve_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Approve admin action
@login_required(login_url='login_adm.html')
def approve_adm_adm_action(request, pk):
    if check_admin(request.user):
        # get information from database
        adm = Admin.objects.get(id=pk)
        adm.status = True  # approve admin
        adm.save()
        messages.add_message(request, messages.INFO, 'Admin approved successfully.')
        return redirect(reverse('approve_adm.html'))
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# View all admins
@login_required(login_url='login_adm.html')
def all_adm_adm_view(request):
    if check_admin(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()
        adm_approved = Admin.objects.all().filter(status=True).count()
        adm_pending = Admin.objects.all().filter(status=False).count()
        adm_count = Admin.objects.all().count()

        # get information from database and render in html webpage
        adm_details = []
        for a in Admin.objects.all():
            adm_details.append(
                [a.id, a.image.url, a.first_name, a.last_name, a.dob, a.address, a.city, a.country, a.postcode,
                 a.status])

        context = {'adm': adm, 'adm_approved': adm_approved,
                   'adm_pending': adm_pending, 'adm_count': adm_count,
                   'adm_details': adm_details}

        return render(request, 'appointments/admin/view_all_adm.html', context)
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Student
def register_cust_view(request):  # Register student
    if request.method == "POST":
        registration_form = StudentRegistrationForm(request.POST, request.FILES)
        if registration_form.is_valid():  # if form is valid
            dob = registration_form.cleaned_data.get('dob')  # get date of birth from form
            if dob < timezone.now().date():  # check if date is valid
                new_user = User.objects.create_user(username=registration_form.cleaned_data.get('username'),
                                                    email=registration_form.cleaned_data.get('email'),
                                                    password=registration_form.cleaned_data.get(
                                                        'password1'))  # create use
                c = Student(student=new_user,
                             first_name=registration_form.cleaned_data.get('first_name'),
                             last_name=registration_form.cleaned_data.get('last_name'),
                             dob=registration_form.cleaned_data.get('dob'),
                             course_name=registration_form.cleaned_data.get('course_name'),
                             student_address=registration_form.cleaned_data.get('student_address'),
                             image=request.FILES['image']
                             )  # create student
                c.save()

                group = Group.objects.get_or_create(name='Student')  # add user to patient group
                group[0].user_set.add(new_user)

                messages.add_message(request, messages.INFO, 'Registration successful!')
                return redirect('login_cust.html')
            else:  # if date of birth is invalid
                registration_form.add_error('dob', 'Invalid date of birth.')
                return render(request, 'appointments/student/register_cust.html',
                              {'registration_form': registration_form})
        else:
            print(registration_form.errors)
    else:
        registration_form = StudentRegistrationForm()
    return render(request, 'appointments/student/register_cust.html', {'registration_form': registration_form})


# Login student
def login_cust_view(request):  # Login student
    if request.method == "POST":
        login_form = AuthenticationForm(request=request, data=request.POST)
        if login_form.is_valid():  # if form is valid
            username = login_form.cleaned_data.get('username')  # get username from form
            password = login_form.cleaned_data.get('password')  # get password from form
            user = auth.authenticate(username=username, password=password)  # get user
            if user is not None and check_student(user):  # if user exists and is a student
                auth.login(request, user)  # login
                account_approval = Student.objects.all().filter(status=True, student_id=request.user.id)
                if account_approval:  # if account is approved
                    return redirect('profile_cust.html')
                else:  # if not approved, redirect to wait_approval webpage
                    messages.add_message(request, messages.INFO, 'Your account is currently pending. '
                                                                 'Please wait for approval.')
                    return render(request, 'appointments/student/login_cust.html', {'login_form': login_form})
        return render(request, 'appointments/student/login_cust.html', {'login_form': login_form})
    else:
        login_form = AuthenticationForm()

    return render(request, 'appointments/student/login_cust.html', {'login_form': login_form})


# Student profile
@login_required(login_url='login_eng.html')
def profile_cust_view(request):
    if check_student(request.user):
        # get information from database and render in html webpage
        cust = Student.objects.filter(student_id=request.user.id).first()
        dob = cust.dob
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))  # calculate age
        if request.method == "POST":
            student_update_form = StudentUpdateForm(request.POST, request.FILES, instance=cust)
            if student_update_form.is_valid():  # if form is valid
                dob = student_update_form.cleaned_data.get('dob')  # get date of birth from form
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                if dob < timezone.now().date():  # if date of birth is valid
                    student_update_form.save()  # save details
                    cust.age = cust  # save age
                    cust.save()

                    messages.add_message(request, messages.INFO, 'Profile updated successfully!')
                    return redirect('profile_cust.html')
                else:
                    student_update_form.add_error('dob', 'Invalid date of birth.')
                    context = {
                        'student_update_form': student_update_form,
                        'cust': cust,
                        'age': age
                    }
                    return render(request, 'appointments/student/profile_cust.html', context)
            else:
                print(student_update_form.errors)
        student_update_form = StudentUpdateForm(instance=cust)
        context = {
            'student_update_form': student_update_form,
            'cust': cust,
            'age': age
        }
        return render(request, 'appointments/student/profile_cust.html', context)
    else:
        auth.logout(request)
        return redirect('login_cust.html')


# Student book appointment
@login_required(login_url='login_eng.html')
def book_app_cust_view(request):
    if check_student(request.user):
        cust = Student.objects.filter(student_id=request.user.id).first()
        app_details = []

        for app in Appointment.objects.filter(student=cust, status=False).all():
            e = app.counsellor
            if e:
                app_details.append([e.first_name, e.last_name, e.service_field,
                                    app.description, app.app_date, app.app_time, app.status])

        if request.method == "POST":  # if student books an appointment
            app_form = StudentAppointmentForm(request.POST)

            if app_form.is_valid():  # if form is valid
                eng_id = int(app_form.cleaned_data.get('counsellor'))  # get counsellor id from form
                eng = Counsellor.objects.all().filter(id=eng_id).first()  # get counsellor from form

                if check_eng_availability(eng,  # check if counsellor is available during that slot
                                          app_form.cleaned_data.get('app_date'),
                                          app_form.cleaned_data.get('app_time')):
                    app_date = app_form.cleaned_data.get('app_date')  # get appointment date
                    if timezone.now().date() < app_date:  # check if appointment date is valid
                        app = Appointment(counsellor=eng,
                                          student=cust,
                                          description=app_form.cleaned_data.get('description'),
                                          app_date=app_form.cleaned_data.get('app_date'),
                                          app_time=app_form.cleaned_data.get('app_time'),
                                          status=False)  # create appointment instance, which is unapproved
                        app.save()
                        messages.add_message(request, messages.INFO, 'Your appointment is received and pending.')
                        return redirect('book_app_cust.html')
                    else:
                        app_form.add_error('app_date', 'Invalid date.')
                else:  # if counsellor is busy
                    app_form.add_error('app_time', 'Slot Unavailable.')
                return render(request, 'appointments/student/book_app_cust.html',
                              {'app_form': app_form, 'app_details': app_details})
            else:  # if form is invalid
                print(app_form.errors)
        else:
            app_form = StudentAppointmentForm()
        return render(request, 'appointments/student/book_app_cust.html',
                      {'cust': cust, 'app_form': app_form, 'app_details': app_details})
    else:
        auth.logout(request)
        return redirect('login_cust.html')


# View student appointment dashboard
@login_required(login_url='login_eng.html')
def app_cust_view(request):
    if check_student(request.user):
        # get information from database and render in html webpage
        cust = Student.objects.filter(student_id=request.user.id).first()

        total_app = Appointment.objects.filter(student=cust).count()
        total_approved_app = Appointment.objects.filter(status=True, student=cust).count()
        total_pending_app = Appointment.objects.filter(status=False, student=cust).count()
        # app_total = Appointment.objects.filter(status=True, student=cust).all()

        pending_appointment_details = []
        for app in Appointment.objects.filter(status=False, completed=False,
                                              student=cust).all():  # get all approved appointments
            e = app.counsellor
            c = app.student
            if e and c:
                pending_appointment_details.append(
                    [e.first_name, e.last_name, e.service_field, c.first_name, c.last_name,
                     app.pk, app.description, app.app_date, app.app_time, app.app_link,
                     app.status, app.completed, app.rating])

        incomplete_appointment_details = []
        for app in Appointment.objects.filter(status=True, completed=False,
                                              student=cust).all():  # get all approved appointments
            e = app.counsellor
            c = app.student
            if e and c:
                incomplete_appointment_details.append(
                    [e.first_name, e.last_name, e.service_field, c.first_name, c.last_name,
                     app.pk, app.description, app.app_date, app.app_time, app.app_link,
                     app.status, app.completed, app.rating])

        appointment_details = []
        for app in Appointment.objects.filter(status=True, student=cust).all():  # get all approved appointments
            e = app.counsellor
            c = app.student
            if e and c:
                appointment_details.append([e.first_name, e.last_name, e.service_field, c.first_name, c.last_name,
                                            app.pk, app.description, app.app_date, app.app_time, app.app_link,
                                            app.status, app.completed, app.rating])

        messages.add_message(request, messages.INFO, 'You have {0} pending appointments.'.format(total_pending_app))

        context = {
            'cust': cust,
            'total_app': total_app,
            'total_approved_app': total_approved_app,
            'total_pending_app': total_pending_app,
            'pending_appointment_details': pending_appointment_details,
            'appointment_details': appointment_details,
            'incomplete_appointment_details': incomplete_appointment_details,
            # 'message': message
        }

        return render(request, 'appointments/student/view_app_cust.html',
                      context)
    else:
        auth.logout(request)
        return redirect('login_cust.html')


# View all student appointments
@login_required(login_url='login_eng.html')
def all_app_cust_view(request):
    if check_student(request.user):
        # get information from database and render in html webpage
        cust = Student.objects.filter(student_id=request.user.id).first()

        total_app = Appointment.objects.filter(student=cust).count()
        total_approved_app = Appointment.objects.filter(status=True, student=cust).count()
        total_pending_app = Appointment.objects.filter(status=False, student=cust).count()
        # app_total = Appointment.objects.filter(status=True, student=cust).all()

        pending_appointment_details = []
        for app in Appointment.objects.filter(status=False, completed=False,
                                              student=cust).all():  # get all approved appointments
            e = app.counsellor
            c = app.student
            if e and c:
                pending_appointment_details.append(
                    [e.first_name, e.last_name, e.service_field, c.first_name, c.last_name,
                     app.pk, app.description, app.app_date, app.app_time, app.app_link,
                     app.status, app.completed, app.rating])

        incomplete_appointment_details = []
        for app in Appointment.objects.filter(status=True, completed=False,
                                              student=cust).all():  # get all approved appointments
            e = app.counsellor
            c = app.student
            if e and c:
                incomplete_appointment_details.append(
                    [e.first_name, e.last_name, e.service_field, c.first_name, c.last_name,
                     app.pk, app.description, app.app_date, app.app_time, app.app_link,
                     app.status, app.completed, app.rating])

        completed_appointment_details = []
        for app in Appointment.objects.filter(status=True, completed=True,
                                              student=cust).all():  # get all approved appointments
            e = app.counsellor
            c = app.student
            if e and c:
                completed_appointment_details.append(
                    [e.first_name, e.last_name, e.service_field, c.first_name, c.last_name,
                     app.pk, app.description, app.app_date, app.app_time, app.app_link,
                     app.status, app.completed, app.rating])

        messages.add_message(request, messages.INFO, 'You have {0} appointments.'.format(total_approved_app))

        context = {
            'cust': cust,
            'total_app': total_app,
            'total_approved_app': total_approved_app,
            'total_pending_app': total_pending_app,
            'pending_appointment_details': pending_appointment_details,
            'completed_appointment_details': completed_appointment_details,
            'incomplete_appointment_details': incomplete_appointment_details,
        }

        return render(request, 'appointments/student/view_all_app_cust.html',
                      context)
    else:
        auth.logout(request)
        return redirect('login_cust.html')


# Appointment rating
@login_required(login_url='login_eng.html')


# View approved appointment's details
@login_required(login_url='login_eng.html')
def app_details_cust_view(request, pk):
    if check_student(request.user):
        app = Appointment.objects.filter(id=pk).first()  # get appointment
        eng = app.counsellor
        cust = app.student

        app.app_link = cust.first_name

        appointment_details = [eng.first_name, eng.last_name, eng.service_field,
                               cust.first_name, cust.last_name,
                               cust.course_name, cust.student_address,
                               app.app_date, app.app_time, app.app_link, app.description,
                               app.status, app.completed, pk]  # render fields
        return render(request, 'appointments/student/view_app_details_cust.html',
                      {
                       'eng': eng,
                       'app': app,
                       'cust': cust,
                       'appointment_details': appointment_details})

        # 'med': med})
    else:
        auth.logout(request)
        return redirect('login_cust.html')


# Join meeting
@login_required(login_url='login_cust.html')
def join_meeting_cust_view(request):
    if check_student(request.user):
        # get information from database and render in html webpage
        cust = Student.objects.get(student_id=request.user.id)
        total_app = Appointment.objects.filter(student=cust).count()
        total_approved_app = Appointment.objects.filter(status=True, student=cust).count()
        total_pending_app = Appointment.objects.filter(status=False, student=cust).count()

        app_details = []
        for app in Appointment.objects.filter(status=True, student=cust,
                                              app_link__isnull=True).all():  # get all approved appointments with room name
            e = app.counsellor
            if e:
                app.app_link = cust.first_name
                app_details.append([app.pk, e.first_name, e.last_name, e.service_field,
                                    app.app_date, app.app_time, app.description, app.app_link, app.status])

        eng_details = []
        for esf in CounsellorServiceField.objects.all():  # get all counsellor service field instances
            e = esf.counsellor
            dob = e.dob
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if e.status:
                eng_details.append([e.first_name, e.last_name, e.service_field, e.city, age,
                                    esf.app_total])

        return render(request, 'appointments/student/join_meeting_cust.html',
                      {'cust': cust, 'total_app': total_app,
                       'total_approved_app': total_approved_app,
                       'total_pending_app': total_pending_app,
                       'app_details': app_details,
                       'eng_details': eng_details})
    else:
        auth.logout(request)
        return redirect('login_cust.html')


# Appointment report
@login_required(login_url='login_eng.html')
def app_report_cust_view(request, pk):
    # get information from database and render in html webpage
    app = Appointment.objects.all().filter(id=pk).first()
    cust = app.student
    eng = app.doctor
    app_date = app.calldate
    app_time = app.calltime

    app_details = []

    context = {
        'cust_name': cust.first_name,
        'eng_name': eng.first_name,
        'app_date': app_date,
        'app_time': app_time,
        'app_desc': app.description,
        'cust_course_name': app.course_name,
        'cust_stud_add': app.student_address,
        'app_details': app_details,
        'pk': pk,
    }

    if check_student(request.user):
        return render(request, 'appointments/student/app_report_cust.html', context)
    # elif check_counsellor(request.user):
    #     return render(request, 'hospital/Doctor/report_apt.html', context)
    # elif check_admin(request.user):
    #     return render(request, 'hospital/Admin/report_apt.html', context)
    else:
        return render(request, 'appointments/account/login.html')


# Student feedback
@login_required(login_url='login_eng.html')
def feedback_cust_view(request):
    if check_student(request.user):
        cust = Student.objects.get(student_id=request.user.id)
        feedback_form = forms.FeedbackForm()
        if request.method == 'POST':
            feedback_form = forms.FeedbackForm(request.POST)
            if feedback_form.is_valid():  # if form is valid
                email = feedback_form.cleaned_data['Email']  # get email from form
                name = feedback_form.cleaned_data['Name']  # get name from form
                subject = "You have a new Feedback from {}:<{}>".format(name, feedback_form.cleaned_data[
                    'Email'])  # get subject from form
                message = feedback_form.cleaned_data['Message']  # get message from form

                message = "Subject: {}\n" \
                          "Date: {}\n" \
                          "Message:\n\n {}" \
                    .format(dict(feedback_form.subject_choices).get(feedback_form.cleaned_data['Subject']),
                            datetime.datetime.now(),
                            feedback_form.cleaned_data['Message'])

                try:
                    mail_admins(subject, message)
                    messages.add_message(request, messages.INFO, 'Thank you for submitting your feedback.')

                    return redirect('feedback_cust.html')
                except:
                    feedback_form.add_error('Email',
                                            'Try again.')
                    return render(request, 'appointments/student/feedback_cust.html', {'email': email,
                                                                                        'name': name,
                                                                                        'subject': subject,
                                                                                        'message': message,
                                                                                        'feedback_form': feedback_form,
                                                                                        'cust': cust})
        return render(request, 'appointments/student/feedback_cust.html', {'feedback_form': feedback_form,
                                                                                        'cust': cust})
    else:
        auth.logout(request)
        return redirect('login_cust.html')


# Download report
def dl_app_report_action(request, pk):
    # get information from database
    template_path = 'appointments/report/app_report_pdf.html'

    app = Appointment.objects.all().filter(id=pk).first()

    cust = app.student
    eng = app.counsellor

    app_date = app.app_date
    app_time = app.app_time

    app_details = []

    context = {
        'cust_name': cust.first_name,
        'eng_name': eng.first_name,
        'app_date': app_date,
        'app_time': app_time,
        'app_desc': app.description,
        'cust_comp_name': app.course_name,
        'cust_comp_add': app.student_address,
        'app_details': app_details,
    }
    # context = {'myvar': 'this is your templates context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="appointment_report.pdf"'
    # find the templates and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


# Counsellor
def register_eng_view(request):  # Register counsellor
    if request.method == "POST":
        registration_form = CounsellorRegistrationForm(request.POST, request.FILES)
        if registration_form.is_valid():  # if form is valid
            dob = registration_form.cleaned_data.get('dob')  # get date of birth from form
            if dob < timezone.now().date():  # if date of birth is valid
                new_user = User.objects.create_user(username=registration_form.cleaned_data.get('username'),
                                                    email=registration_form.cleaned_data.get('email'),
                                                    password=registration_form.cleaned_data.get(
                                                        'password1'))  # create new user
                eng = Counsellor(counsellor=new_user,
                               first_name=registration_form.cleaned_data.get('first_name'),
                               last_name=registration_form.cleaned_data.get('last_name'),
                               service_field=registration_form.cleaned_data.get('service_field'),
                               dob=registration_form.cleaned_data.get('dob'),
                               address=registration_form.cleaned_data.get('address'),
                               city=registration_form.cleaned_data.get('city'),
                               country=registration_form.cleaned_data.get('country'),
                               postcode=registration_form.cleaned_data.get('postcode'),
                               image=request.FILES['image'])  # create new counsellor
                eng.save()

                esf = CounsellorServiceField(counsellor=eng)  # appfees=200, admfees=2000)
                esf.save()

                group = Group.objects.get_or_create(name='Counsellor')  # add user to doctor group
                group[0].user_set.add(new_user)

                messages.add_message(request, messages.INFO, 'Registration successful!')
                return redirect('login_eng.html')
            else:  # if date of birth is invalid
                registration_form.add_error('dob', 'Invalid date of birth.')
                return render(request, 'appointments/counsellor/register_eng.html',
                              {'registration_form': registration_form})
        else:
            print(registration_form.errors)
    else:
        registration_form = CounsellorRegistrationForm()

    return render(request, 'appointments/counsellor/register_eng.html', {'registration_form': registration_form})


# Login counsellor
def login_eng_view(request):
    if request.method == "POST":
        login_form = AuthenticationForm(request=request, data=request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            user = auth.authenticate(username=username, password=password)
            if user is not None and check_counsellor(user):
                auth.login(request, user)
                account_approval = Counsellor.objects.all().filter(status=True, counsellor_id=request.user.id)
                if account_approval:
                    return redirect('profile_eng.html')
                else:
                    messages.add_message(request, messages.INFO, 'Your account is currently pending. '
                                                                 'Please wait for approval.')
                    return render(request, 'appointments/counsellor/login_eng.html', {'login_form': login_form})
        return render(request, 'appointments/counsellor/login_eng.html', {'login_form': login_form})
    else:
        login_form = AuthenticationForm()
    return render(request, 'appointments/counsellor/login_eng.html', {'login_form': login_form})


# Counsellor profile
@login_required(login_url='login_eng.html')
def profile_eng_view(request):
    if check_counsellor(request.user):
        # get information from database and render in html webpage
        eng = Counsellor.objects.filter(counsellor_id=request.user.id).first()
        dob = eng.dob
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))  # calculate age
        if request.method == "POST":
            counsellor_update_form = CounsellorUpdateForm(request.POST, request.FILES, instance=eng)
            if counsellor_update_form.is_valid():  # if form is valid
                dob = counsellor_update_form.cleaned_data.get('dob')
                today = date.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))  # calculate age
                if dob < timezone.now().date():  # if date of birth is valid
                    counsellor_update_form.save()
                    esf = CounsellorServiceField.objects.all().filter(
                        counsellor=eng).first()  # get doctor professional details
                    # dp.appfees = p_form.cleaned_data.get('appfees')
                    # dp.admfees = p_form.cleaned_data.get('admfees')
                    esf.save()  # save counsellor service field data

                    messages.add_message(request, messages.INFO, 'Profile updated successfully!')
                    return redirect('profile_eng.html')
                else:
                    counsellor_update_form.add_error('dob', 'Invalid date of birth.')
                    context = {
                        'counsellor_update_form': counsellor_update_form,
                        'eng': eng,
                        'age': age
                    }
                    return render(request, 'appointments/counsellor/profile_eng.html', context)
        else:
            # get data from database and put initial values in form
            # age.refresh_from_db()
            esf = CounsellorServiceField.objects.all().filter(counsellor=eng).first()
            counsellor_update_form = CounsellorUpdateForm(instance=eng)
            # counsellor_update_form.fields['appfees'].initial = dp.appfees
            # counsellor_update_form.fields['admfees'].initial = dp.admfees
            context = {
                'counsellor_update_form': counsellor_update_form,
                'eng': eng,
                'age': age
            }
            return render(request, 'appointments/counsellor/profile_eng.html', context)
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# Counsellor dashboard - approved appointments don't show, WHAT IS WRONG?!
@login_required(login_url='login_eng.html')
def dashboard_eng_view(request):
    if check_counsellor(request.user):
        # get information from database and render in html webpage
        eng = Counsellor.objects.get(counsellor_id=request.user.id)
        app_completed = Appointment.objects.all().filter(counsellor=eng, completed=True).count()
        available_app = Appointment.objects.all().filter(counsellor=eng, status=False).count()
        pending_app_count = Appointment.objects.all().filter(counsellor=eng, status=False).count()
        app_count = models.Appointment.objects.all().filter(status=True, counsellor=eng).count()

        pending_app = []
        for app in Appointment.objects.filter(status=False, counsellor=eng.id, app_link__isnull=True,
                                              completed=False).all():  # get unapproved appointments which have links not set and are not yet finished
            c = Student.objects.filter(id=app.student.id).first()
            if c:
                pending_app.append([app.pk, c.first_name, c.last_name, c.course_name,
                                    app.app_date, app.app_time, app.description, app.status, app.completed])

        upcoming_app = []
        for app in Appointment.objects.filter(status=True, counsellor=eng.id, app_link__isnull=True,
                                              completed=False).all():  # get approved appointments which have links not set and are not yet finished
            c = Student.objects.filter(id=app.student.id).first()
            app.app_link = c.first_name
            if c:
                upcoming_app.append([app.pk, c.first_name, c.last_name, c.course_name,
                                     app.app_date, app.app_time, app.description, app.app_link, app.status,
                                     app.completed,
                                     eng.first_name])

        completed_app = []  # approved manually inside
        for app in Appointment.objects.filter(counsellor=eng, completed=True).all():  # get all approved appointments
            c = app.student
            if c:
                completed_app.append([eng.first_name,
                                      c.first_name,
                                      app.completed, app.pk])

        messages.add_message(request, messages.INFO, 'You have {0} pending appointments to approve.'.format(pending_app_count))

        return render(request, 'appointments/counsellor/dashboard_eng.html',
                      {'eng': eng,
                       'pending_app': pending_app,
                       'upcoming_app': upcoming_app,
                       'app_completed': app_completed,
                       'available_app': available_app,
                       'completed_app': completed_app,
                       'app_count': app_count})
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# View all counsellor appointments
@login_required(login_url='login_eng.html')
def all_app_eng_view(request):
    if check_counsellor(request.user):
        # get information from database and render in html webpage
        eng = Counsellor.objects.get(counsellor_id=request.user.id)
        app_completed = Appointment.objects.all().filter(counsellor=eng.id, completed=True).count()
        available_app = Appointment.objects.all().filter(counsellor=eng.id, status=False).count()
        app_count = models.Appointment.objects.all().filter(counsellor=eng.id, status=True,).count()

        pending_app = []
        for app in Appointment.objects.filter(status=False, counsellor=eng.id, app_link__isnull=True,
                                              completed=False).all():  # get unapproved appointments which have links not set and are not yet finished
            c = Student.objects.filter(id=app.student.id).first()
            if c:
                pending_app.append([app.pk, c.first_name, c.last_name, c.course_name,
                                    app.app_date, app.app_time, app.description, app.status, app.completed])

        upcoming_app = []
        for app in Appointment.objects.filter(status=True, counsellor=eng.id, app_link__isnull=True,
                                              completed=False).all():  # get approved appointments which have links not set and are not yet finished
            c = Student.objects.filter(id=app.student.id).first()
            app.app_link = c.first_name
            if c:
                upcoming_app.append([app.pk, c.first_name, c.last_name, c.course_name,
                                     app.app_date, app.app_time, app.description, app.app_link, app.status,
                                     app.completed,
                                     eng.first_name])

        completed_app = []  # approved manually inside
        for app in Appointment.objects.filter(counsellor=eng.id, completed=True).all():  # get all approved appointments
            c = app.student
            app.app_link = c.first_name
            if c:
                completed_app.append([app.pk, c.first_name, c.last_name, c.course_name,
                                      app.app_date, app.app_time, app.description, app.app_link, app.status,
                                      app.completed,
                                      eng.first_name])

        return render(request, 'appointments/counsellor/view_app_eng.html', {
            'eng': eng,
            'pending_app': pending_app,
            'upcoming_app': upcoming_app,
            'completed_app': completed_app,
            'app_completed': app_completed,
            'app_count': app_count,
            'available_app': available_app, })
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# Add appointment link action - can't seem to save link.... link = app_link?
@login_required(login_url='login_eng.html')
def add_link_eng_action(request, pk, link):
    if check_counsellor(request.user):
        # get information from database and render in html webpage
        appointment = Appointment.objects.get(id=pk)
        appointment.app_link = link
        appointment.save()
        return redirect(reverse('view_app_eng.html'))
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# View counsellor appointment's details, approve appointment or edit details - save & update doesn't work, complete works
@login_required(login_url='login_eng.html')
def app_details_eng_view(request, pk):
    if check_counsellor(request.user):
        adm = Admin.objects.filter(admin_id=request.user.id).first()

        app = Appointment.objects.filter(id=pk).first()  # get appointment
        eng = app.counsellor
        cust = app.student

        app.app_link = cust.first_name

        appointment_details = [eng.first_name, eng.last_name, eng.service_field,
                               cust.first_name, cust.last_name,
                               cust.course_name, cust.student_address,
                               app.app_date, app.app_time, app.app_link, app.description,
                               app.status, app.completed, pk]  # render fields

        return render(request, 'appointments/counsellor/view_app_details_eng.html',
                      {'adm': adm,
                       'eng': eng,
                       'app': app,
                       'cust': cust,
                       'appointment_details': appointment_details})
    else:
        auth.logout(request)
        return redirect('login_adm.html')


# Get an appointment
@login_required(login_url='login_eng.html')
def get_link_eng_action(request, pk):
    if check_counsellor(request.user):
        # get information from database
        appointment = Appointment.objects.get(id=pk)
        appointment.status = True  # approve appointment
        appointment.save()

        eng = appointment.counsellor
        esf = CounsellorServiceField.objects.filter(counsellor=eng).first()
        esf.app_total += 1  # add student to counsellor count
        esf.save()

        messages.add_message(request, messages.INFO, 'Appointment approved!')
        return redirect(reverse('dashboard_eng.html'))
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# Complete an appointment - did I even use this?
@login_required(login_url='login_eng.html')
def complete_app_eng_action(request, pk):
    if check_counsellor(request.user):
        # get information from database and render in html webpage
        app = Appointment.objects.get(id=pk)
        app.completed = True
        app.save()

        messages.add_message(request, messages.INFO, 'Appointment completed successfully!')
        return redirect('view_app_eng.html')
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# View all approved appointments
@login_required(login_url='login_eng.html')
def approved_app_eng_view(request):
    if check_counsellor(request.user):
        eng = Counsellor.objects.get(counsellor_id=request.user.id)  # get counsellor

        incomplete_appointments = []
        for aca in ApprovedStudentAppointment.objects.filter(
                counsellor=eng).all():  # get all students approved under this counsellor
            cust = aca.student
            if cust and not aca.completed_date:
                incomplete_appointments.append([eng.first_name, cust.first_name,
                                                aca.approval_date, aca.completed_date, aca.pk])

        completed_appointments = []
        for aca in ApprovedStudentAppointment.objects.filter(
                counsellor=eng).all():  # get all students approved under this counsellor
            cust = aca.student
            if cust and aca.completed_date:
                completed_appointments.append([eng.first_name, cust.first_name,
                                               aca.approval_date, aca.completed_date, aca.pk])
        return render(request, 'appointments/counsellor/view_approved_app_eng.html',
                      {'incomplete_appointments': incomplete_appointments,
                       'completed_appointments': completed_appointments})
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# View approved appointment's details
@login_required(login_url='login_eng.html')
def approved_app_details_eng_view(request, pk):
    if check_counsellor(request.user):
        # get information from database and render in html webpage
        aca = ApprovedStudentAppointment.objects.filter(id=pk).first()
        eng_d = Counsellor.objects.get(counsellor_id=request.user.id)
        eng_d = eng_d.service_field

        cust = aca.student
        eng = aca.counsellor
        approved_appointment_details = [aca.pk, eng.first_name,
                                        cust.first_name, aca.approval_date, aca.completed_date, aca.description]
        # med = Medicines.objects.all()
        return render(request, 'appointments/counsellor/view_approved_app_details_eng.html',
                      {'approved_appointment_details': approved_appointment_details,
                       'eng_d': eng_d, })
        # 'med': med})
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# Counsellor feedback
@login_required(login_url='login_eng.html')
def feedback_eng_view(request):
    if check_counsellor(request.user):
        eng = Counsellor.objects.get(counsellor_id=request.user.id)
        feedback_form = forms.FeedbackForm()
        if request.method == 'POST':
            feedback_form = forms.FeedbackForm(request.POST)
            if feedback_form.is_valid():  # if form is valid
                email = feedback_form.cleaned_data['Email']  # get email from form
                name = feedback_form.cleaned_data['Name']  # get name from form
                subject = "You have a new Feedback from {}:<{}>".format(name, feedback_form.cleaned_data[
                    'Email'])  # get subject from form
                message = feedback_form.cleaned_data['Message']  # get message from form

                message = "Subject: {}\n" \
                          "Date: {}\n" \
                          "Message:\n\n {}" \
                    .format(
                    dict(feedback_form.subject_choices).get(feedback_form.cleaned_data['Subject']),
                    datetime.datetime.now(),
                    feedback_form.cleaned_data['Message']
                )

                try:
                    mail_admins(subject, message)
                    messages.add_message(request, messages.INFO, 'Thank you for submitting your feedback.')

                    return redirect('feedback_eng.html')
                except:
                    feedback_form.add_error('Email',
                                            'Try again.')
                    return render(request, 'appointments/counsellor/feedback_eng.html', {'feedback_form': feedback_form})
        return render(request, 'appointments/counsellor/feedback_eng.html', {'eng': eng, 'feedback_form': feedback_form})
    else:
        auth.logout(request)
        return redirect('login_eng.html')


# User check
def check_admin(user):  # check if user is admin
    return user.groups.filter(name='Admin').exists()


def check_student(user):  # check if user is student
    return user.groups.filter(name='Student').exists()


def check_counsellor(user):  # check if user is counsellor
    return user.groups.filter(name='Counsellor').exists()


# Appointment availability check
def check_eng_availability(counsellor, dt, tm):  # check if counsellor is available in a given slot
    tm = tm[:-3]  # separate AM/PM
    hr = tm[:-3]  # get hour reading
    mn = tm[-2:]  # get minute reading
    ftm = time(int(hr), int(mn), 0)  # create a time object
    app = Appointment.objects.all().filter(status=True,
                                           counsellor=counsellor,
                                           app_date=dt)  # get all appointments for a given eng and the given date

    if ftm < time(9, 0, 0) or ftm > time(17, 0, 0):  # if time is not in between 9AM to 5PM, reject
        return False

    if time(12, 0, 0) < ftm < time(13, 0, 0):  # if time is in between 12PM to 1PM, reject
        return False

    for a in app:
        if ftm == a.app_time and dt == a.app_date:  # if some other appointment has the same slot, reject
            return False

    return True

from django.contrib import admin

from website.models import Admin, Student, Counsellor, CounsellorServiceField, Appointment, \
    ApprovedStudentAppointment

admin.site.register(Admin)
admin.site.register(Student)
admin.site.register(Counsellor)
admin.site.register(CounsellorServiceField)
admin.site.register(Appointment)
#  admin.site.register(ApprovedStudentAppointment)

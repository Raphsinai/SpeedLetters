from django.contrib import admin
from .models import Newsletter, Email, Subscriber, Unsubscription, Transaction

# Register your models here.

admin.site.register(Newsletter)
admin.site.register(Email)
admin.site.register(Subscriber)
admin.site.register(Unsubscription)
admin.site.register(Transaction)
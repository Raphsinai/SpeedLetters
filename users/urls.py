from django.urls import path
from .views import *

urlpatterns = [
    path('sign-up/', signup, name='sign-up'),
    path('log-in/', loginPage, name='login'),
    path('log-out/', logoutPage, name='logout'),
    path('account/', accountPage, name='account'),
    path('account/validate/email', confirmEmail, name='confirmsignup'),
    path('account/validate/email/resend', resendConfirm, name='confirmemailresend'),
    path('account/general/update', generalUpdate, name='generalUpdate'),
    path('account/personal/update', personalUpdate, name='personalUpdate'),
]
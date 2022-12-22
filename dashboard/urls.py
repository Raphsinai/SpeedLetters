from django.urls import path
from .views import *

urlpatterns = [
    path('', newsletterPage, name='newsletters'),
    path('newsletter/<int:id>', newsletterDetail, name='newsletterDetail'),
    path('newsletter/<int:id>/emails', moreEmail, name='moreEmail'),
    path('newsletter/create', createNewsletter, name='createNewsletter'),
    path('send-email/', sendEmail, name="sendEmail"),
    path('email-detail/<int:id>', emailDetail, name="emailDetail"),
    path('credit/', credit, name='credit'),
    path('credit/buy', buyCredit, name='addCredit'),
    path('credit/data', creditData, name='creditData'),
    path('credit/buy/success', success, name='success'),
    path('credit/buy/cancel', cancel, name='cancel'),
    path('send-email/confirm/<int:id>', mail_confirm, name='confirmEmail'),
]
from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('privacy/', privacy, name='privacy'),
    path('contact/', contact, name='contact'),
    path('subscribe/<int:id>', sub, name='subscribe'),
    path('unsubscribe/<int:id>', unsub, name='unsubscribe'),
]
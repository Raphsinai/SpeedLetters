from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from itertools import chain
from bs4 import BeautifulSoup

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('credit', 1000000)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField('username', max_length=25, unique=True)
    first_name = models.CharField('first name', max_length=200)
    last_name = models.CharField('last name', max_length=200)
    dob = models.DateField('date of birth')
    phone = models.CharField('phone number', max_length=15)
    company = models.CharField('company name', max_length=200)
    email = models.EmailField('email address', unique=True)
    validated_email = models.BooleanField(default=False)
    credit = models.FloatField('credit available', default=0)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [username, first_name, last_name, dob, phone, company]

    objects = UserManager()

    def send_validation(self):
        context = {
            'user': self
        }
        template = render_to_string('users/emailconfirm.html', context=context)
        text = BeautifulSoup(template, 'html.parser').get_text()
        send_mail('Confirm email address - SpeedLetters', text, 'SpeedLetters <noreply.speedletters@gmail.com>', [self.email], True, html_message=template)
        
    def save(self, *args, **kwargs):
        if not self.validated_email:
            self.send_validation()
        super(User, self).save(*args, **kwargs)

    @property
    def emails(self):
        mails = []
        for newsletter in self.newsletter_set.all():
            mails.append(newsletter.email_set.all())
        return (chain(*mails))
    
    @property
    def trans_history(self):
        history = chain(self.transaction_set.all(), self.emails)
        return sorted(history, key=lambda x: x.date_sent if 'date_sent' in dir(x) else x.date, reverse=True)

    def __str__(self):
        return self.email
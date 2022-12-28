from django.db import models
from users.models import User
from django.utils import timezone
from datetime import timedelta
from django.core import mail
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from bs4 import BeautifulSoup
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your models here

class Newsletter(models.Model):
    name = models.CharField(max_length=200)
    opens = models.IntegerField(default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    reply_to = models.EmailField()
    signup_message = models.TextField(default='')

    @property
    def week_sub(self):
        return self.subscriber_set.filter(date_joined__gte=timezone.now()-timedelta(days=7)).count()

    @property
    def week_unsub(self):
        return self.unsubscription_set.filter(date__gte=timezone.now()-timedelta(days=7)).count()

    def __str__(self) -> str:
        return f"{self.name} | {self.creator.username}"

class Email(models.Model):
    subject = models.CharField(max_length=200)
    content_html = models.TextField(null=True)
    content_text = models.TextField(null=True)
    origin = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    date_sent = models.DateTimeField(auto_now_add=True)
    sent = models.BooleanField(default=False)
    amnt_sent = models.IntegerField(null=True)

    @property
    def cost(self):
        num = self.origin.subscriber_set.count()
        if num <= 500:
            return 0.01*num
        elif num <= 1000:
            return 0.007*num
        elif num <= 1500:
            return 0.005*num
        else:
            return 0.003*num
    
    @property
    def amount(self):
        return -self.cost
    
    @property
    def status(self):
        return 'Sent' if self.sent else 'Not yet sent'
    
    @property
    def trans_desc(self):
        return f"Email sent to {self.amnt_sent} inboxes"

    def send(self):
        if not self.sent:
            connection = mail.get_connection()

            connection.open()
            reciever_list = self.origin.subscriber_set.filter(is_recv=True)
            self.amnt_sent = len(reciever_list)
            if "{{ firstName }}" in self.content_html or "{{ lastName }}" in self.content_html:
                for reciever in reciever_list:
                    cont_html = self.content_html.replace('{{ firstName }}', reciever.first_name).replace('{{ lastName }}', reciever.last_name)
                    cont_text = self.content_text.replace('{{ firstName }}', reciever.first_name).replace('{{ lastName }}', reciever.last_name)
                    email = mail.EmailMultiAlternatives(self.subject, cont_text, f'{self.origin.name} <{self.origin.reply_to}>',
                                        [reciever.email], connection=connection, reply_to=[self.origin.reply_to])
                    email.attach_alternative(cont_html, 'text/html')
                    email.send()
            else:
                email = mail.EmailMultiAlternatives(self.subject, self.content_text, f'{self.origin.name} <{self.origin.reply_to}>',
                                        bcc=[reciever.email for reciever in reciever_list], connection=connection, reply_to=[self.origin.reply_to])
                email.attach_alternative(self.content_html, 'text/html')
                email.send()
            connection.close()
            self.sent = True
            self.date_sent = timezone.now()
            self.save()

    def save(self, html=None, css=None, js=None, *args, **kwargs):
        if html is not None:
            if '<head>' not in html:
                html = '<head></head>' + html
            html = BeautifulSoup(html, 'html.parser')
            if css is not None:
                html.head.append(BeautifulSoup(f'<style>{css}</style>', 'html.parser'))
            if js is not None:
                html.body.append(BeautifulSoup(f'<script type="text/js">{js}</script>', 'html.parser'))
            self.content_html = str(html)
            self.content_text = html.get_text()
        super(Email, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.subject} | {self.origin.name}"

    class Meta:
        ordering = ['-date_sent']

class Subscriber(models.Model):
    first_name = models.CharField(max_length=200, verbose_name='First name')
    last_name = models.CharField(max_length=200, verbose_name="Last name")
    email = models.EmailField()
    subscription = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)
    consent_date = models.DateTimeField(null=True)
    is_recv = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} | {self.subscription.name}"

    def save(self, confirm: bool = False, *args, **kwargs):
        if confirm:
            context = {
                'sub': self,
            }
            template = render_to_string('main/signup_confirm_email.html', context=context)
            text = BeautifulSoup(template, 'html.parser').get_text()
            send_mail(f'Confirm signup to {self.subscription.name}', text, f'{self.subscription.name} <{self.subscription.reply_to}>', [self.email], True, html_message=template)
        super(Subscriber, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_recv = False
        self.save()

    class Meta:
        unique_together = ('email', 'subscription',)

class Unsubscription(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    subscription = models.ForeignKey(Newsletter, on_delete=models.PROTECT)
    prev = models.ForeignKey(Subscriber, on_delete=models.PROTECT, null=True)

    def __str__(self) -> str:
        return f'{self.prev.email} | {self.subscription.name}'

class Transaction(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    checkout_id = models.CharField(max_length=200)
    customer = models.ForeignKey(User, on_delete=models.PROTECT)
    added = models.BooleanField(default=False)

    @property
    def checkout_session(self):
        return stripe.checkout.Session.retrieve(self.checkout_id)

    @property
    def payment_intent(self):
        return stripe.PaymentIntent.retrieve(self.checkout_session.payment_intent)
    
    @property
    def amount(self):
        return self.payment_intent.amount/100

    @property
    def status(self):
        return self.payment_intent.status

    @property
    def trans_desc(self):
        return f"Purchased {self.amount} credit"
    
    def add_credit(self):
        if self.status == 'succeeded' and self.added == False:
            self.customer.credit += self.amount
            self.customer.save()
            self.added = True
            self.save()

    def __str__(self) -> str:
        return f"{self.customer.username} | {self.payment_intent.amount}"
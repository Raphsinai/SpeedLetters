from django.shortcuts import render
from .models import Message
from dashboard.models import Subscriber, Newsletter, Unsubscription
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import IntegrityError
from django.http import HttpResponseNotFound
from django.core.validators import validate_email 

# Create your views here.

def index(request):
    context = {
        "title": "Home",
    }
    return render(request, 'main/index.html', context)

def privacy(request):
    return render(request, 'main/privacy.html')

def contact(request):
    if request.method == "POST":
        context = {
            "title": "Contact",
            "msg": True,
            "good": True,
            "msg_content": "Your message has been sent and we will get back to you asap."
        }
        for _, item in request.POST.items():
            if item == '':
                context['good'] = False
                context['msg_content'] = "Please fill in every input"
                return render(request, 'main/contact.html', context)
        
        msg = Message(
            title   = request.POST['title'],
            email   = request.POST['email'],
            content = request.POST['content']
        )
        msg.save()

        return render(request, 'main/contact.html', context)

    else:
        context = {
            'title': 'Contact',
        }
        return render(request, 'main/contact.html', context)

def sub(request, id):
    try:
        newsletter = Newsletter.objects.get(id=id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('- requested newsletter does not exist')
    context = {
        'title': f'Subscribe to {newsletter.name}',
        'msg': False,
        'newsletter': newsletter
    }
    if request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['subemail']
        try:
            validate_email(email)
        except ValidationError:
            context['msg'] = True
            context['msg_content'] = 'Email is not valid'
            return render(request, 'main/sub.html', context)
        sub = Subscriber(first_name=fname, last_name=lname, email=email, subscription=newsletter)
        try:
            sub.save()
        except IntegrityError:
            context['msg'] = True
            context['msg_content'] = 'Email is already subscribed'
            return render(request, 'main/sub.html', context)
        context['title'] = context['title'].replace('Subscribe', 'Subscribed')
        context['subscriber'] = sub
        return render(request, 'main/subbed.html', context)
    return render(request, 'main/sub.html', context)
        
def unsub(request, id):
    try:
        n = Newsletter.objects.get(id=id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound('- newsletter does not exist')
    context = {
        'title': f'Unsubscribe from {n.name}',
        'msg': False,
        'newsletter': n
    }
    if request.method == "POST":
        email = request.POST['unsubemail']
        try:
            validate_email(email)
        except ValidationError:
            context['msg'] = True
            context['msg_content'] = 'Email is not valid'
            return render(request, 'main/unsub.html', context)
        try:
            sub = Subscriber.objects.get(email=email, subscription=n)
        except ObjectDoesNotExist:
            context['msg'] = True
            context['msg_content'] = 'Email is not subscribed'
            return render(request, 'main/unsub.html', context)
        if not sub.is_recv:
            context['msg'] = True
            context['msg_content'] = 'Email is not subscribed'
            return render(request, 'main/unsub.html', context)
        unsub = Unsubscription(subscription=n, prev=sub)
        unsub.save()
        sub.delete()
        context['unsub'] = unsub
        return render(request, 'main/unsubbed.html', context)
    return render(request, 'main/unsub.html', context)

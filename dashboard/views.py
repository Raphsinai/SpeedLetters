from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound, HttpResponseForbidden, JsonResponse
from .models import Newsletter, Email, Transaction
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.template.defaultfilters import date, time
from threading import Thread
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your views here.

def newsletterPage(request):
    context = {
        "title": "Newsletters"
    }
    return render(request, 'dashboard/newsletters.html', context)

def newsletterDetail(request, id):
    try:
        newsletter = Newsletter.objects.get(id=id)
        if newsletter.creator.id != request.user.id:
            HttpResponseForbidden()
        context = {
            'title': newsletter.name,
            'newsletter': newsletter
        }
        return render(request, 'dashboard/newsletter_detail.html', context=context)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()

def moreEmail(request, id):
    try:
        n = Newsletter.objects.get(id=id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()
    if n.creator.id != request.user.id:
        return HttpResponseForbidden()
    if 'amnt' in request.GET:
        try:
            amount = int(request.GET['amnt'])
        except ValueError:
            return HttpResponseNotFound()
        emails = n.email_set.all()[amount:amount+10]
        data = {
            "emails": [{'id': email.id, 'subject': email.subject, 'status': email.status, 'date': f'{date(email.date_sent)}, {time(email.date_sent)}'} for email in emails]
        }
        return JsonResponse(data)

def createNewsletter(request):
    context = {
        'title': 'Create Newsletter'
    }
    if request.method == "POST":
        name = request.POST["name"]
        reply_to = request.POST["reply_to"]
        n = Newsletter(name=name, reply_to=reply_to, creator=request.user)
        n.save()
        return redirect('newsletterDetail', n.id)
    return render(request, 'dashboard/create_newsletter.html', context)

def sendEmail(request):
    if request.method == "POST":
        context = {
            'msg': False,
            'title': "Send Email"
        }
        m = Email(subject=request.POST['subject'], origin=Newsletter.objects.get(id=request.POST['newsletter']))
        if len(request.FILES) != 0:
            html = request.FILES.read().decode()
            css, js = '', ''
        else:
            html = request.POST['html']
            css = request.POST['css']
            js = request.POST['js']

        m.save(html=html, css=css, js=js)
        
        return redirect('confirmEmail', m.id)
    
    context = {
        'msg': False,
        'title': "Send email",
        'selected': int(request.GET['id']) if 'id' in request.GET else None,
    }
    return render(request, 'dashboard/send_mail.html', context)

def mail_confirm(request, id):
    if request.method == "POST":
        m = Email.objects.get(id=int(request.POST['id']))
        if request.user.credit < m.cost:
            context['msg'] = True
            context['msg_content'] = 'Insufficient credit'
            m.delete()
            return render(request, 'dashboard/send_mail.html', context)
        request.user.credit -= m.cost
        request.user.save()

        t = Thread(target=m.send)
        t.setDaemon(False)
        t.start()
        return redirect('emailDetail', m.id)
    
    context = {
        'title': 'Confirm send',
    }
    try:
        mail = Email.objects.get(id=id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound
    context['email'] = mail
    return render(request, 'dashboard/mail_confirm.html', context)

def emailDetail(request, id):
    email = Email.objects.get(id=id)
    context = {
        "title": email.subject,
        'email': email,
    }
    return render(request, 'dashboard/email_detail.html', context)

def credit(request):
    context = {
        'title': 'Manage Credit'
    }
    res = render(request, 'dashboard/credit.html', context)
    return res

def creditData(request):
    data = {}
    for i, trans in enumerate(request.user.trans_history):
        data[i] = [trans.trans_desc, trans.amount]
    return JsonResponse(data)

def buyCredit(request):
    if request.method == "POST":
        amount = int(request.POST["amount"])
        if amount < 5: amount = 5
        try:
            session = stripe.checkout.Session.create(
                line_items = [
                    {
                        'price': 'price_1MH4i2K3hm4Enp4Us7HDEm4G',
                        'quantity': amount,
                    },
                ],
                mode='payment',
                success_url=f'{request.scheme}://{request.get_host()}'+'/dashboard/credit/buy/success?id={CHECKOUT_SESSION_ID}',
                cancel_url=f'{request.scheme}://{request.get_host()}/dashboard/credit',
            )
        except Exception as e:
            print(str(e))
            return redirect('addCredit')
        trans = Transaction(checkout_id=session.id, customer=request.user)
        trans.save()
        return redirect(session.url)
    context = {
        "title": 'Buy more credit'
    }
    return render(request, 'dashboard/add_credit.html', context)

def success(request):
    context = {
        "title": 'Success',
    }
    if 'id' in request.GET:
        checkout_id = request.GET['id']
        trans = Transaction.objects.get(checkout_id=checkout_id)
        if trans.customer == request.user:
            trans.add_credit()
            context['trans'] = trans
    return render(request, 'dashboard/success.html', context)

def cancel(request):
    context = {
        "title": 'Cancelled'
    }
    return render(request, 'dashboard/cancel.html', context)
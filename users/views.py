from django.shortcuts import render, redirect
from .models import User
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.middleware import csrf
from datetime import date
# Create your views here.

def signup(request):
    if request.user.is_authenticated:
        return redirect('newsletters')
    if request.method == "POST":
        context = {
            "title": "Sign up",
            "msg":  True,
        }
        for _, item in request.POST.items():
            if item == '':
                context["msg_content"] = "Please fill in every input"
                return render(request, 'users/signup.html', context)

        if not re.match(r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}", request.POST["password"]):
            context["msg_content"] = "Invalid password"
            return render(request, 'users/signup.html', context)
        try:
            validate_email(request.POST['email'])
        except ValidationError:
            context["msg_content"] = "Invalid email"
            return render(request, 'users/signup.html', context)
        if User.objects.filter(email=request.POST["email"]).exists():
            context["msg_content"] = "Email is already taken"
            return render(request, 'users/signup.html', context)
        if User.objects.filter(username=request.POST["username"]).exists():
            context["msg_content"] = "Username is already taken"
            return render(request, 'users/signup.html', context)

        new_user = User.objects.create_user(
            username    = request.POST['username'],
            first_name  = request.POST['firstName'],
            last_name   = request.POST['lastName'],
            dob         = request.POST['dob'],
            phone       = "00"+request.POST['code']+request.POST['phone'],
            company     = request.POST['company'],
            email       = request.POST['email'],
            password    = request.POST['password']
        )
        new_user.save()

        ## TODO: email verification: TODO ##

        login(request, new_user)
        return redirect('newsletters')
    else:
        context = {
            "title": "Sign up",
        }
        return render(request, 'users/signup.html', context)

@csrf_exempt
def confirmEmail(request):
    if request.method == "POST":
        user = User.objects.get(id=int(request.POST['id']))
        user.validated_email = True
        user.save()
        context = {
            'title': 'Email verified'
        }
        return render(request, 'users/validated.html', context)
    return HttpResponseBadRequest()

def resendConfirm(request, id):
    user = User.objects.get(id=id)
    user.send_validation()
    context = {
        'title': 'Validation email resent',
    }
    return render(request, 'users/validation_sent.html', context)

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('newsletters')
    if request.method == "POST":
        user = authenticate(request, email=request.POST["email"], password=request.POST["password"])
        if not user:
            context = {
                "title": "Log in",
                "msg":  True,
                "msg_content": "Credentials are invalid, check email/password"
            }
            return render(request, 'users/login.html', context)
        login(request, user)
        return redirect('newsletters')
    else:
        context = {
            "title": "Log in"
        }
        return render(request, 'users/login.html', context)

def logoutPage(request):
    logout(request)
    return redirect('index')

def accountPage(request):
    context = {
        'title': 'Account',
    }
    return render(request, 'users/account.html', context)

def generalUpdate(request):
    if request.method == "POST":
        resData = {
            'success': True,
            'desc': '',
            'csrf': None,
        }
        if request.POST['email'] != request.user.email and request.POST['email'] != '':
            email = request.POST['email']
            try:
                validate_email(email)
            except ValidationError:
                resData['success'] = False
                resData['desc'] += 'Not a valid email address' if resData['desc'] == '' else '<br>Not a valid email address'
                ## TODO: email verification: TODO ##
                return JsonResponse(resData)
            request.user.email = request.POST['email']
            request.user.save()
            resData['desc'] += 'Email updated successfully' if resData['desc'] == '' else '<br>Email updated successfully'
        if request.POST['oldpwd'] != '' or request.POST['newpwd'] != '':
            if not check_password(request.POST['oldpwd'], request.user.password):
                resData['success'] = False
                resData['desc'] += 'Old password is wrong' if resData['desc'] == '' else '<br>Old password is wrong'
                return JsonResponse(resData)
            if request.POST['newpwd'] != request.POST['newpwdrepeat']:
                resData['success'] = False
                resData['desc'] += 'New passwords do not match' if resData['desc'] == '' else '<br>New passwords do not match'
                return JsonResponse(resData)
            if not re.match(r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}", request.POST["newpwd"]):
                resData["success"] = False
                resData["desc"] += 'New password does not fit criteria' if resData['desc'] == '' else '<br>New password does not fit criteria'
                return JsonResponse(resData)
            request.user.set_password(request.POST['newpwd'])
            request.user.save()
            login(request, request.user)
            token = csrf.get_token(request)
            resData['csrf'] = token
            resData['desc'] += 'Password changed successfully' if resData['desc'] == '' else '<br>Password changed successfully'
        return JsonResponse(resData)
    return HttpResponseBadRequest()

def personalUpdate(request):
    if request.method == 'POST':
        resData = {
            'success': True,
            'desc': 'Details updated'
        }
        if request.POST['first_name'] != request.user.first_name and request.POST['first_name'] != '':
            request.user.first_name = request.POST['first_name']
            request.user.save()
        if request.POST['last_name'] != request.user.last_name and request.POST['last_name'] != '':
            request.user.last_name = request.POST['last_name']
            request.user.save()
        if request.POST['company'] != request.user.company and request.POST['company'] != '':
            request.user.company = request.POST['company']
            request.user.save()
        if request.POST['phone'] != request.user.phone and request.POST['phone'] != '':
            request.user.phone = request.POST['phone']
            request.user.save()
        if request.POST['dob'] != '':
            inputDate = date(*[int(i) for i in request.POST['dob'].split('-')])
            if inputDate != request.user.dob:
                request.user.dob = inputDate
                request.user.save()

        return JsonResponse(resData)
            
    return HttpResponseBadRequest()
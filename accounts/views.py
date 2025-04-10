import random
import string
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.urls import reverse_lazy

from .forms import *
from .models import *
from .tokens import *


logger = logging.getLogger(__name__)
User = get_user_model()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email, otp, expiry_seconds=300):
    cache.set(f'otp_{email}', otp, timeout=expiry_seconds)

def get_stored_otp(email):
    return cache.get(f'otp_{email}')

def delete_stored_otp(email):
    cache.delete(f'otp_{email}')
    
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            UserProfile.objects.create(user=user)  # Create user profile

            # Send activation email
            current_site = get_current_site(request)
            subject = 'Activate Your Account'
            message = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            send_mail(subject, strip_tags(message), settings.EMAIL_HOST_USER, [user.email], html_message=message)

            messages.success(request, 'Please check your email to activate your account.')
            return redirect('accounts:login')  
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_email_verified = True
        user.save()
        login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend') 
        messages.success(request, 'Your account has been activated. You are now logged in.')
        return redirect('store:home')  
    else:
        messages.error(request, 'The activation link is invalid or has expired.')
        return redirect('accounts:login')

def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)                
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(request, username=username_or_email, password=password)        
        if user:
            if not user.is_active:
                messages.error(request, 'This account is not active. Please check your email for activation link.')
                return redirect('accounts:login')
            
            if not user.is_email_verified:
                messages.error(request, 'Please verify your email before login.')
                return redirect('accounts:login')
            otp = generate_otp()
            store_otp(user.email, otp)
            
            subject = 'Your Login OTP'
            message = f'Your OTP for login is: {otp} and it will be expired in next 5 min'
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
            )
            
            request.session['temp_user_email'] = user.email
            
            return render(request, 'registration/otp_verification.html', {
                'form': OTPVerificationForm(),
                'email': user.email
            })
        else:
            messages.error(request, 'Invalid username or password.')
            
    form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def verify_otp(request):
    email = request.session.get('temp_user_email')
    if not email:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data.get('otp')            
            stored_otp = get_stored_otp(email)
            logger.info(f"Verifying OTP for {email}. Entered: {otp}, Stored: {stored_otp}")
            
            if stored_otp == otp:
                try:
                    user = User.objects.get(email=email)
                    login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
                    delete_stored_otp(email)
                    request.session.pop('temp_user_email', None)

                    if user.first_login:
                        return redirect('accounts:complete_profile')
                    return redirect('store:home')
                except User.DoesNotExist:
                    messages.error(request, 'User not found.')
            else:
                logger.warning(f"Invalid OTP for {email}. Entered: {otp}, Stored: {stored_otp}")
                messages.error(request, 'Invalid OTP. Please try again.')
        
    else:
        form = OTPVerificationForm()
        
    return render(request, 'registration/otp_verification.html', {
        'form': form,
        'email': request.session.get('temp_user_email')
    })

def resend_otp(request):
    email = request.session.get('temp_user_email')
    if not email:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('accounts:login')

    otp = get_stored_otp(email)
    if not otp:
        otp = generate_otp()
        store_otp(email, otp)

    send_mail(
        'Your Resend OTP',
        f'Your OTP is: {otp} and it will be expired soon',
        settings.EMAIL_HOST_USER,
        [email],
    )

    messages.success(request, 'OTP has been resent to your email.')
    return redirect('accounts:verify_otp')

  
@login_required
def complete_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            request.user.first_login = False
            request.user.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('store:home')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/complete_profile.html', {'form': form,'profile': profile})

@login_required
def profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/edit_profile.html', {'form': form, 'profile': profile})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('store:home')

def home(request):
    return render(request, 'store/home.html')



class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url=reverse_lazy('accounts:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
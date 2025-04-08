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

# OTP handling (using cache)
OTP_STORE = {}  # For local testing only. Remove in production.

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email, otp):
    cache.set(f'otp_{email}', otp, timeout=300)  # 5 minutes
    OTP_STORE[email] = otp  # For local testing. Remove in production.

def get_stored_otp(email):
    otp = cache.get(f'otp_{email}')
    if not otp and settings.DEBUG:  # Only check OTP_STORE in DEBUG mode
        otp = OTP_STORE.get(email)
    return otp


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
        print(f"Attempting login with {username_or_email}")
        
        # Check if the input is an email
        if '@' in username_or_email:
            try:
                # Get the user object using the email
                user_obj = User.objects.get(email=username_or_email)
                print(f"Found user by email: {user_obj.username}")
                
                # Authenticate the user using the username and password
                user = authenticate(request, username=user_obj.username, password=password)
                print(f"Auth with username={user_obj.username}: {user}")
            except User.DoesNotExist:
                user = None
        else:
            # Authenticate the user using the username and password
            user = authenticate(request, username=username_or_email, password=password)
            print(f"Auth with username={username_or_email}: {user}")
        
        print(f"Final authentication result: {user}")
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'This account is not active. Please check your email for activation link.')
                return redirect('accounts:login')
            
            if not user.is_email_verified:
                messages.error(request, 'Please verify your email before login.')
                return redirect('accounts:login')
            
            # Rest of your code for OTP generation and verification
            # Continue with OTP generation and verification...
            otp = generate_otp()
            store_otp(user.email, otp)
            
            # Send OTP to user's email
            subject = 'Your Login OTP'
            message = f'Your OTP for login is: {otp}'
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [user.email],
            )
            
            # Store user temporarily
            request.session['temp_user_email'] = user.email
            
            return render(request, 'registration/otp_verification.html', {
                'form': OTPVerificationForm(),
                'email': user.email
            })
        else:
            messages.error(request, 'Invalid username or password.')
            
    # If not POST or authentication failed, show the login form
    form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def verify_otp(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data.get('otp')
            email = request.session.get('temp_user_email')
            
            stored_otp = get_stored_otp(email)
            logger.info(f"Verifying OTP for {email}. Entered: {otp}, Stored: {stored_otp}")
            
            if email and stored_otp and stored_otp == otp:
                # OTP verified, log in user
                logger.info(f"OTP verified for {email}")
                user = User.objects.get(email=email)
                print(user)
                login(request, user, backend='accounts.backends.EmailOrUsernameModelBackend')
                cache.delete(f'otp_{email}')  # Remove OTP after use
                if email in OTP_STORE:
                    del OTP_STORE[email]  # Also clean up the dictionary
                del request.session['temp_user_email']
                
                # Check if first login
                if user.first_login:
                    return redirect('accounts:complete_profile')
                return redirect('store:home')
            else:
                logger.warning(f"Invalid OTP for {email}. Entered: {otp}, Stored: {stored_otp}")
                messages.error(request, 'Invalid OTP. Please try again.')
        
        return render(request, 'registration/otp_verification.html', {
            'form': form,
            'email': request.session.get('temp_user_email')
        })
    
    return redirect('accounts:login')

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
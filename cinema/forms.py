from django import forms
from django.contrib.auth.models import User
from .models import Movie, Cinema, Showtime

class RegisterForm(forms.Form):
    full_name = forms.CharField(label='full name', max_length=100)
    phone_number = forms.CharField(label='phone number', max_length=20)
    email = forms.CharField(label='email', max_length=100)
    password = forms.CharField(label='password', max_length=50)
    confirm_password = forms.CharField(label='confirm password', max_length=50)
    
    # 1. Custom Validation: Tự động kiểm tra Email đã tồn tại chưa
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email này đã được đăng ký trên hệ thống!")
        return email

    # 2. Custom Validation: Tự động kiểm tra 2 mật khẩu có khớp nhau không
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Mật khẩu xác nhận không khớp!")
        
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.CharField(label='email', max_length=100)
    password = forms.CharField(label='password', max_length=50)


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'duration', 'genres', 'description', 'rating', 'actors', 'poster_url', 'banner_url']
        widgets = {
            'genres': forms.CheckboxSelectMultiple(),
        }

class CinemaForm(forms.ModelForm):
    class Meta:
        model = Cinema
        fields = ['name', 'location', 'image']

class ShowtimeForm(forms.ModelForm):
    class Meta:
        model = Showtime
        fields = ['movie', 'room', 'start_time', 'end_time', 'base_price']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'block w-full px-4 py-3 bg-background border border-border rounded-xl text-white placeholder-subtext/50 text-sm focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'block w-full px-4 py-3 bg-background border border-border rounded-xl text-white placeholder-subtext/50 text-sm focus:ring-2 focus:ring-primary focus:border-transparent transition-all'
            }),
        }

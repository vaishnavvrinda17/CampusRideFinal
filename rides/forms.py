
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import StudentProfile


class StudentRegistrationForm(UserCreationForm):
    username = forms.CharField(
    max_length=150,
    required=True,
    label="Username"
    )
    email = forms.EmailField(
    required=True,
    label="College Email",
    help_text="Use your official @ipsacademy.org email address."
    )
    enrollment_number = forms.CharField(
        max_length=30,
        required=True,
        label="Enrollment Number"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "enrollment_number",
            "password1",
            "password2",
        ]

    
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if not email.endswith("@ipsacademy.org"):
            raise forms.ValidationError(
                "Please use your official IPS Academy email address."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email



    def clean_enrollment_number(self):
        enrollment_number = self.cleaned_data["enrollment_number"].strip()

        if StudentProfile.objects.filter(
            enrollment_number__iexact=enrollment_number
        ).exists():
            raise forms.ValidationError(
                "This enrollment number is already registered."
            )

        return enrollment_number


from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .models import UserProfile
from .utils import resize


class UserProfileEditionForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, label="first name", required=False)
    last_name = forms.CharField(max_length=100, label="last name", required=False)

    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name", "picture"]

    # Picture resizing before store it in DB
    def clean_picture(self):
        avatar = self.cleaned_data["picture"]
        previous_avatar = None

        try:
            previous_avatar= UserProfile.objects.get(id=self.instance.id).picture
        except self.Meta.model.DoesNotExist:
            pass

        # check if has new avatar to resize (if avatar),
        # if profile has no old avatar (not previous_avatar) -> resize,
        # else check if new avatar, is really new, but not old version of itself (avatar.name != previous_avatar.name)
        if avatar and (not previous_avatar or avatar.name != previous_avatar.name):
            return resize(avatar)
        return avatar

    # Override save to store first/last names from form to UserProfile.owner directly
    def save(self, commit=True):
        if self.errors:
            raise ValueError(self.errors)

        profile = super(UserProfileEditionForm, self).save(commit=commit)
        data = self.cleaned_data

        owner = profile.owner
        owner.first_name = data["first_name"]
        owner.last_name = data["last_name"]

        if commit:
            owner.save()
        return profile


class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label="first name", required=False)
    last_name = forms.CharField(max_length=100, label="last name", required=False)
    email = forms.CharField(max_length=100, help_text="your_address@domain.com")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        field_classes = {"username": UsernameField}

    def clean_email(self):
        email = self.cleaned_data["email"]

        try:
            validate_email(email)
            if not User.objects.all().filter(email=email):
                return email
            raise ValidationError("We have a user with such email already... ")

        except ValidationError as e:
            raise ValidationError(e.message)

    def save(self, commit=True):
        if self.errors:
            raise ValueError(self.errors)

        user = super(UserSignUpForm, self).save(commit=False)
        data = self.cleaned_data

        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.email = data["email"]

        profile = UserProfile()
        profile.owner = user

        if commit:
            user.save()
            profile.save()
        return user

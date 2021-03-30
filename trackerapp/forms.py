from django import forms
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms.fields import ChoiceField, DateField
from django.core.files.images import get_image_dimensions
from .resize_img import resize

from .models import TaskModel, UserProfile
from django.core.validators import validate_email


class DateInput(forms.DateInput):
    input_type = "date"


class TaskSortingForm(forms.Form):
    """
    Form to filter task by date(from-till) and by status
    """

    from_date = DateField(
        label="date from:",
        widget=DateInput,
        help_text="Format like 03.17.1979",
        required=False,
    )
    till_date = DateField(
        label="date to:",
        widget=DateInput,
        help_text="Format like 03.17.1979",
        required=False,
    )

    STATUS_CHOICE_LIST = list(TaskModel.LOAN_STATUS)
    STATUS_CHOICE_LIST.append(("", "-----"))

    choose_status = ChoiceField(
        label="choose status", choices=STATUS_CHOICE_LIST, required=False
    )

    def clean(self):
        data = super().clean()
        from_date = data.get("from_date")
        till_date = data.get("till_date")

        if from_date and till_date:
            if from_date > till_date:
                raise ValidationError('"date from" must be before "till date"')
        return data


class MessageSortingForm(forms.Form):
    """
    Form to filter message by date(from-till)
    """

    from_date = DateField(
        label="date from:",
        widget=DateInput,
        help_text="Format like 03.17.1979",
        required=False,
    )
    till_date = DateField(
        label="date to:",
        widget=DateInput,
        help_text="Format like 03.17.1979",
        required=False,
    )


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, label="first name", required=False)
    last_name = forms.CharField(max_length=100, label="last name", required=False)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'picture']

    def clean_email(self):
        email = self.cleaned_data["email"]

        try:
            validate_email(email)
            return email
        except ValidationError:
            raise ValidationError("Invalid email address.")

    def clean_picture(self):
        avatar = self.cleaned_data["picture"]
        max_width = max_height = 500

        if avatar:
            return resize(avatar)

        return avatar

    def save(self, commit=True):
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )

        profile = super(UserProfileForm, self).save(commit=commit)
        data = self.cleaned_data

        owner = profile.owner
        owner.first_name = data['first_name']
        owner.last_name = data['last_name']

        if commit:
            owner.save()
        return profile


class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label="first name", required=False)
    last_name = forms.CharField(max_length=100, label="last name", required=False)
    email = forms.CharField(max_length=100, label="your_address@domain.com")

    class Meta:
        model = User
        fields = ["username", 'first_name', 'last_name', 'email']
        field_classes = {'username': UsernameField}

    def clean_email(self):
        email = self.cleaned_data["email"]

        try:
            validate_email(email)
            return email
        except ValidationError:
            raise ValidationError("Invalid email address.")

    def save(self, commit=True):
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )

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

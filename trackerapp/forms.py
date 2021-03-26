from django import forms
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.forms.fields import ChoiceField, DateField
from .models import TaskModel, UserProfile


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
    class Meta:
        model = UserProfile
        fields = ["owner", "picture"]
    def clean_avatar(self):
        avatar = self.cleaned_data["avatar"]

        try:
            w, h = get_image_dimensions(avatar)

            # validate dimensions
            max_width = max_height = 150
            if w > max_width or h > max_height:
                raise forms.ValidationError(
                    u"Please use an image that is "
                    "%s x %s pixels or smaller." % (max_width, max_height)
                )

            # validate content type
            main, sub = avatar.content_type.split("/")
            if not (main == "image" and sub in ["jpeg", "pjpeg", "gif", "png"]):
                raise forms.ValidationError(u"Please use a JPEG, " "GIF or PNG image.")

            # validate file size
            if len(avatar) > (20 * 1024):
                raise forms.ValidationError(u"Avatar file size may not exceed 20k.")

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return avatar

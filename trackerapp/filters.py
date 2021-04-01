from trackerapp.forms import DateSortingForm, TaskSortingForm


def date_filter(obj, message_list):
    """
    date_filter - to filter list of messages by values from form
    """
    if obj.request.method == "POST":
        sorting_form = DateSortingForm(obj.request.POST)

        if sorting_form.is_valid():
            date_from = sorting_form.cleaned_data["from_date"]
            date_till = sorting_form.cleaned_data["till_date"]

            if date_from:
                message_list = message_list.filter(creation_date__gte=date_from)

            if date_till:
                message_list = message_list.filter(creation_date__lte=date_till)

        else:
            DateSortingForm()
    return message_list


def task_filter(obj, tasklist):
    """
    task_filter - to filter list of task by values from form
    """
    if obj.request.method == "POST":
        sorting_form = TaskSortingForm(obj.request.POST)

        if sorting_form.is_valid():
            date_from = sorting_form.cleaned_data["from_date"]
            date_till = sorting_form.cleaned_data["till_date"]
            choose_status = sorting_form.cleaned_data["choose_status"]

            if date_from:
                tasklist = tasklist.filter(creation_date__gte=date_from)

            if date_till:
                tasklist = tasklist.filter(creation_date__lte=date_till)

            if choose_status:
                tasklist = tasklist.filter(status__exact=choose_status)
        else:
            TaskSortingForm()
    return tasklist

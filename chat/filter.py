from chat.forms import RoomSortingForm


def room_list_filter(list_view_instance, list_to_filter):
    if list_view_instance.request.method == "POST":
        sorting_form = RoomSortingForm(list_view_instance.request.POST)

        if sorting_form.is_valid():
            name = sorting_form.cleaned_data["name"]
            is_private = sorting_form.cleaned_data["is_private"]

            if name:
                list_to_filter = list_to_filter.filter(name__icontains=name)

            if is_private:
                list_to_filter = list_to_filter.filter(is_private=is_private)

        else:
            RoomSortingForm()
    return list_to_filter

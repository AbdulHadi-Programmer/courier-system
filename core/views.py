from django.shortcuts import render, redirect


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'core/home.html')

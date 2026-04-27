from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from .forms import MahasiswaRegistrationForm


def register_view(request):
    if request.method == "POST":
        form = MahasiswaRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Secara otomatis login setelah register sukses
            login(request, user)
            return redirect("/")
    else:
        form = MahasiswaRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


def logout_view(request):
    logout(request)
    # Sesi pengguna otomatis dihancurkan oleh Django setelah logout [cite: 40]
    return redirect("accounts:login")

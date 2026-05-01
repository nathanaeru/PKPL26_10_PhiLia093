from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from .forms import (
    MahasiswaRegistrationForm,
    CustomAuthenticationForm,
    StaffRegistrationForm,
    StaffAuthenticationForm,
)


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


def staff_register_view(request):
    if request.method == "POST":
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("forum:landing")
    else:
        form = StaffRegistrationForm()

    return render(request, "accounts/staff_register.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = CustomAuthenticationForm

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        # Buat kunci pelacakan unik per username
        cache_key = f"login_attempts_{username}"
        attempts = cache.get(cache_key, 0)

        # Jika sudah 5 kali gagal, tolak proses login sepenuhnya
        if attempts >= 5:
            form = self.get_form()
            form.add_error(
                None,
                "Akun terkunci sementara karena 5x percobaan gagal. Silakan tunggu 15 menit.",
            )
            return self.form_invalid(form)

        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        # Jika login gagal (password salah, dll), tambah jumlah percobaan
        username = self.request.POST.get("username")
        if username:
            cache_key = f"login_attempts_{username}"
            attempts = cache.get(cache_key, 0)
            # Simpan jumlah kegagalan di memori selama 15 menit (900 detik)
            cache.set(cache_key, attempts + 1, 900)
        return super().form_invalid(form)

    def form_valid(self, form):
        # Jika login berhasil sebelum kena limit, bersihkan riwayat kegagalan
        username = self.request.POST.get("username")
        if username:
            cache_key = f"login_attempts_{username}"
            cache.delete(cache_key)
        return super().form_valid(form)


class StaffLoginView(CustomLoginView):
    # Menggunakan template khusus staf
    template_name = "accounts/staff_login.html"
    # Menggunakan form login yang mewajibkan kode akses
    form_class = StaffAuthenticationForm


def logout_view(request):
    logout(request)
    # Sesi pengguna otomatis dihancurkan oleh Django setelah logout
    return redirect("accounts:login")

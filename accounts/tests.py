from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

from .forms import StaffRegistrationForm
from . import views

from .models import CustomUser


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        # Setup ini dijalankan SEBELUM setiap test dimulai
        self.client = Client()

        # Buat akun mahasiswa bohongan
        self.mahasiswa = CustomUser.objects.create_user(
            username="mhs_uji",
            email="mhs@ui.ac.id",
            password="passwordKuat123",
            role="mahasiswa",
        )

        # Buat akun dosen bohongan
        self.dosen = CustomUser.objects.create_user(
            username="dosen_uji",
            email="dosen@ui.ac.id",
            password="passwordKuat123",
            role="dosen",
        )

        # Buat akun asisten dosen bohongan
        self.asdos = CustomUser.objects.create_user(
            username="asdos_uji",
            email="asdos@ui.ac.id",
            password="passwordKuat123",
            role="asisten_dosen",
        )

    def tearDown(self):
        # Bersihkan cache setelah test selesai agar tidak bentrok
        cache.clear()

    def test_rate_limiting_lockout(self):
        """Uji coba apakah akun terkunci setelah 5x gagal login"""
        login_url = reverse("accounts:login")

        # Lakukan 5x percobaan gagal (sengaja salahkan password)
        for i in range(5):
            response = self.client.post(
                login_url, {"username": "mhs_uji", "password": "passwordSalah"}
            )
            # Pastikan masih bisa mencoba (kembali ke halaman login dengan form)
            self.assertEqual(response.status_code, 200)

        # Percobaan ke-6 (sekalipun menggunakan password yang BENAR kali ini)
        response_locked = self.client.post(
            login_url, {"username": "mhs_uji", "password": "passwordKuat123"}
        )

        # Harus tetap ditolak karena sudah masuk masa lockout
        self.assertEqual(response_locked.status_code, 200)
        # Cek apakah pesan lockout kita benar-benar muncul di HTML
        self.assertContains(
            response_locked, "Akun terkunci sementara karena 5x percobaan gagal"
        )

    def test_staff_rate_limiting_lockout(self):
        """Uji coba apakah portal login staf juga terkunci setelah 5x gagal"""
        # Gunakan nama URL routing untuk portal staf
        staff_login_url = reverse("accounts:staff_login")

        # Lakukan 5x percobaan gagal di portal staf
        for i in range(5):
            response = self.client.post(
                staff_login_url,
                {
                    "username": "dosen_uji",
                    "password": "passwordSalah",
                    # Jangan lupa kirimkan kode akses, misal asal-asalan saja
                    "access_code": "KODE_SALAH",
                },
            )
            self.assertEqual(response.status_code, 200)

        # Percobaan ke-6 (menggunakan kredensial dan kode .env yang BENAR sekalipun)
        response_locked = self.client.post(
            staff_login_url,
            {
                "username": "dosen_uji",
                "password": "passwordKuat123",
                "access_code": settings.DOSEN_ACCESS_CODE,
            },
        )

        # Harus tetap ditolak karena sistem rate limit dari CustomLoginView ikut bekerja di sini
        self.assertEqual(response_locked.status_code, 200)
        self.assertContains(
            response_locked, "Akun terkunci sementara karena 5x percobaan gagal"
        )

    def test_portal_isolation_dosen_cannot_use_public_login(self):
        """Uji coba Dosen login lewat portal Mahasiswa (harus ditolak dengan pesan umum)"""
        login_url = reverse("accounts:login")

        # Dosen login di portal publik dengan kredensial BENAR
        response = self.client.post(
            login_url, {"username": "dosen_uji", "password": "passwordKuat123"}
        )

        # Cek apakah ditolak
        self.assertEqual(response.status_code, 200)
        # Cek apakah pesannya disamarkan (mencegah enumerasi)
        self.assertContains(response, "Nama pengguna atau kata sandi salah.")

        # Pastikan user tersebut benar-benar TIDAK login di sesi tersebut
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_portal_isolation_asdos_cannot_use_public_login(self):
        """Uji coba Asdos login lewat portal Mahasiswa (harus ditolak dengan pesan umum)"""
        login_url = reverse("accounts:login")

        response = self.client.post(
            login_url, {"username": "asdos_uji", "password": "passwordKuat123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nama pengguna atau kata sandi salah.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_mahasiswa_can_use_public_login(self):
        """Uji coba Mahasiswa dapat login lewat portal publik dengan kredensial benar"""
        login_url = reverse("accounts:login")

        response = self.client.post(
            login_url, {"username": "mhs_uji", "password": "passwordKuat123"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.mahasiswa.id)

    def test_portal_isolation_mahasiswa_cannot_use_staff_login(self):
        """Uji coba Mahasiswa login lewat portal Staf (harus ditolak dengan pesan umum)"""
        staff_login_url = reverse("accounts:staff_login")

        # Mahasiswa login di portal staf dengan kredensial BENAR
        response = self.client.post(
            staff_login_url,
            {
                "username": "mhs_uji",
                "password": "passwordKuat123",
                "access_code": settings.DOSEN_ACCESS_CODE,  # Kode akses benar tapi role salah
            },
        )

        # Cek apakah ditolak
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kredensial atau kode akses salah.")

        # Pastikan user tersebut benar-benar TIDAK login di sesi tersebut
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_dosen_can_use_staff_login(self):
        """Uji coba Dosen dapat login lewat portal staf dengan kode akses dosen"""
        staff_login_url = reverse("accounts:staff_login")

        response = self.client.post(
            staff_login_url,
            {
                "username": "dosen_uji",
                "password": "passwordKuat123",
                "access_code": settings.DOSEN_ACCESS_CODE,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("forum:landing"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.dosen.id)

    def test_asdos_can_use_staff_login_with_dosen_code(self):
        """Uji coba Asdos dapat login lewat portal staf memakai kode dosen yang juga valid"""
        staff_login_url = reverse("accounts:staff_login")

        response = self.client.post(
            staff_login_url,
            {
                "username": "asdos_uji",
                "password": "passwordKuat123",
                "access_code": settings.DOSEN_ACCESS_CODE,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("forum:landing"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.asdos.id)

    def test_staff_login_rejects_invalid_access_code(self):
        """Uji coba portal staf menolak kode akses yang tidak dikenal"""
        staff_login_url = reverse("accounts:staff_login")

        response = self.client.post(
            staff_login_url,
            {
                "username": "dosen_uji",
                "password": "passwordKuat123",
                "access_code": "KODE_TIDAK_VALID",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kode akses staf tidak valid.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_registration_with_dosen_code_sets_dosen_role(self):
        """Uji coba registrasi staf dengan kode dosen menghasilkan role dosen"""
        staff_register_url = reverse("accounts:staff_register")

        response = self.client.post(
            staff_register_url,
            {
                "username": "dosen_baru",
                "email": "dosen_baru@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": settings.DOSEN_ACCESS_CODE,
            },
        )

        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(username="dosen_baru")
        self.assertEqual(user.role, "dosen")
        self.assertTrue(user.check_password("passwordKuat123"))

    def test_staff_registration_rejects_invalid_access_code(self):
        """Uji coba registrasi staf menolak kode akses yang tidak dikenal"""
        form = StaffRegistrationForm(
            data={
                "username": "staf_invalid",
                "email": "staf_invalid@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": "KODE_TIDAK_VALID",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("access_code", form.errors)
        self.assertContains(
            self.client.post(
                reverse("accounts:staff_register"),
                {
                    "username": "staf_invalid",
                    "email": "staf_invalid@ui.ac.id",
                    "password1": "passwordKuat123",
                    "password2": "passwordKuat123",
                    "access_code": "KODE_TIDAK_VALID",
                },
            ),
            "Kode akses tidak valid atau tidak dikenali.",
        )

    def test_staff_registration_with_asdos_code_sets_asdos_role(self):
        """Uji coba registrasi staf dengan kode asdos menghasilkan role asisten_dosen"""
        staff_register_url = reverse("accounts:staff_register")

        response = self.client.post(
            staff_register_url,
            {
                "username": "asdos_baru",
                "email": "asdos_baru@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": settings.ASDOS_ACCESS_CODE,
            },
        )

        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(username="asdos_baru")
        self.assertEqual(user.role, "asisten_dosen")
        self.assertTrue(user.check_password("passwordKuat123"))

    def test_mahasiswa_registration_post_logs_user_in(self):
        """Uji coba registrasi mahasiswa via POST membuat akun dan login otomatis"""
        register_url = reverse("accounts:register")

        response = self.client.post(
            register_url,
            {
                "username": "mhs_baru",
                "email": "mhs_baru@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.assertTrue(CustomUser.objects.filter(username="mhs_baru").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_mahasiswa_registration_view_get_renders_form(self):
        """Uji coba halaman registrasi mahasiswa untuk request GET"""
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daftar sebagai Mahasiswa")

    def test_staff_registration_form_save_commit_false(self):
        """Uji coba save(commit=False) tetap menyiapkan role sebelum disimpan"""
        form = StaffRegistrationForm(
            data={
                "username": "asdos_commit_false",
                "email": "asdos_commit_false@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": settings.ASDOS_ACCESS_CODE,
            }
        )

        self.assertTrue(form.is_valid())
        user = form.save(commit=False)
        self.assertEqual(user.role, "asisten_dosen")
        self.assertIsNone(user.pk)

    def test_register_view_get_renders_form(self):
        """Uji coba halaman registrasi mahasiswa untuk request GET"""
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daftar sebagai Mahasiswa")

    def test_staff_register_view_get_renders_form(self):
        """Uji coba halaman registrasi staf untuk request GET"""
        response = self.client.get(reverse("accounts:staff_register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kode Akses Staf")

    def test_logout_view_redirects_and_clears_session(self):
        """Uji coba logout menghapus sesi dan mengarahkan ke login mahasiswa"""
        self.client.login(username="mhs_uji", password="passwordKuat123")
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.get(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_custom_user_str_returns_username(self):
        """Uji coba representasi string user memakai username"""
        self.assertEqual(str(self.mahasiswa), "mhs_uji")

    def test_staff_login_view_uses_staff_template(self):
        """Uji coba view login staf memakai form dan template staf"""
        response = self.client.get(reverse("accounts:staff_login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/staff_login.html")

    def test_custom_login_view_uses_public_template(self):
        """Uji coba view login publik memakai template mahasiswa"""
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_staff_login_view_class_configuration(self):
        """Uji coba konfigurasi class-based view login staf"""
        self.assertEqual(
            views.StaffLoginView.template_name, "accounts/staff_login.html"
        )
        self.assertIs(views.StaffLoginView.form_class, views.StaffAuthenticationForm)

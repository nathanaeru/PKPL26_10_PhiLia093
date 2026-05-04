from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings

from .forms import StaffRegistrationForm
from . import views
from .models import CustomUser


class AuthenticationSecurityTests(TestCase):
    """
    Kelas ini fokus untuk menguji portal publik (Mahasiswa) dan
    pemenuhan Test Case dasar sesuai dokumen keamanan.
    """

    def setUp(self):
        self.client = Client()
        self.login_url = reverse("accounts:login")

        # Akun valid untuk pengujian fungsional dan isolasi
        self.mahasiswa_valid = CustomUser.objects.create_user(
            username="mhs_valid",
            email="mhs_valid@ui.ac.id",
            password="PasswordAman123",
            role="mahasiswa",
        )
        self.dosen_uji = CustomUser.objects.create_user(
            username="dosen_uji",
            email="dosen@ui.ac.id",
            password="passwordKuat123",
            role="dosen",
        )
        self.asdos_uji = CustomUser.objects.create_user(
            username="asdos_uji",
            email="asdos@ui.ac.id",
            password="passwordKuat123",
            role="asisten_dosen",
        )

    def tearDown(self):
        cache.clear()

    # PEMENUHAN TEST CASE (Sesuai Dokumen)

    def test_tc_sqli_01_login_bypass(self):
        """TC-SQLi-01: Memastikan login tidak bisa di-bypass dengan payload SQLi"""
        response = self.client.post(
            self.login_url, {"username": "' OR '1'='1' --", "password": "bebas"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nama pengguna atau kata sandi salah.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_tc_ba_01_password_hashing(self):
        """TC-BA-01: Memastikan password tersimpan dalam bentuk hash"""
        user_db = CustomUser.objects.get(username="mhs_valid")
        self.assertNotEqual(user_db.password, "PasswordAman123")
        self.assertTrue(user_db.password.startswith("pbkdf2_sha256$"))

    def test_tc_ba_02_rate_limiting(self):
        """TC-BA-02: Memastikan sistem mengunci akun setelah 5x percobaan gagal"""
        for i in range(5):
            self.client.post(
                self.login_url, {"username": "mhs_valid", "password": f"WrongPass{i}"}
            )

        # Percobaan ke-6 dengan password benar tetap ditolak
        response = self.client.post(
            self.login_url,
            {"username": "mhs_valid", "password": "PasswordAman123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Akun terkunci sementara karena 5x percobaan gagal"
        )

    def test_tc_ba_03_session_invalidation(self):
        """TC-BA-03: Memastikan sesi dihapus setelah logout"""
        self.client.login(username="mhs_valid", password="PasswordAman123")
        self.assertIn("_auth_user_id", self.client.session)

        self.client.get(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_tc_ba_05_generic_error_message(self):
        """TC-BA-05: Memastikan pesan error seragam (mencegah enumerasi)"""
        resp_wrong_user = self.client.post(
            self.login_url, {"username": "user_ga_ada", "password": "PasswordAman123"}
        )
        resp_wrong_pass = self.client.post(
            self.login_url, {"username": "mhs_valid", "password": "SalahPassword"}
        )
        self.assertContains(resp_wrong_user, "Nama pengguna atau kata sandi salah.")
        self.assertContains(resp_wrong_pass, "Nama pengguna atau kata sandi salah.")

    def test_tc_csrf_01_token_presence(self):
        """TC-CSRF-01: Memastikan form POST memiliki token CSRF"""
        response = self.client.get(self.login_url)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_tc_csrf_02_invalid_csrf_token(self):
        """TC-CSRF-02: Memastikan server menolak POST request (HTTP 403) jika token CSRF salah"""
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            self.login_url,
            {
                "username": "mhs_valid",
                "password": "PasswordAman123",
                "csrfmiddlewaretoken": "invalid_token_12345",
            },
        )
        self.assertEqual(response.status_code, 403)

    # PENGUJIAN ISOLASI PORTAL & FUNGSIONALITAS

    def test_portal_isolation_dosen_cannot_use_public_login(self):
        """Dosen tidak boleh menggunakan portal Mahasiswa"""
        response = self.client.post(
            self.login_url, {"username": "dosen_uji", "password": "passwordKuat123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nama pengguna atau kata sandi salah.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_portal_isolation_asdos_cannot_use_public_login(self):
        """Asisten Dosen tidak boleh menggunakan portal Mahasiswa"""
        response = self.client.post(
            self.login_url, {"username": "asdos_uji", "password": "passwordKuat123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nama pengguna atau kata sandi salah.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_mahasiswa_can_use_public_login(self):
        """Mahasiswa dapat login lewat portal publik"""
        response = self.client.post(
            self.login_url, {"username": "mhs_valid", "password": "PasswordAman123"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_mahasiswa_registration_post_logs_user_in(self):
        """Registrasi mahasiswa via POST membuat akun dan login otomatis"""
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "mhs_baru",
                "email": "mhs_baru@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CustomUser.objects.filter(username="mhs_baru").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_view_get_renders_form(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daftar sebagai Mahasiswa")

    def test_custom_user_str_returns_username(self):
        self.assertEqual(str(self.mahasiswa_valid), "mhs_valid")


@override_settings(
    DOSEN_ACCESS_CODE="TEST_DOSEN_CODE", ASDOS_ACCESS_CODE="TEST_ASDOS_CODE"
)
class StaffAuthenticationSecurityTests(TestCase):
    """
    Kelas ini khusus menguji keamanan dan alur portal internal Staf.
    """

    def setUp(self):
        self.client = Client()
        self.staff_login_url = reverse("accounts:staff_login")
        self.staff_register_url = reverse("accounts:staff_register")

        self.dosen_uji = CustomUser.objects.create_user(
            username="dosen_uji",
            email="dosen@ui.ac.id",
            password="passwordKuat123",
            role="dosen",
        )
        self.asdos_uji = CustomUser.objects.create_user(
            username="asdos_uji",
            email="asdos@ui.ac.id",
            password="passwordKuat123",
            role="asisten_dosen",
        )
        self.mhs_uji = CustomUser.objects.create_user(
            username="mhs_uji",
            email="mhs@ui.ac.id",
            password="passwordKuat123",
            role="mahasiswa",
        )

    def tearDown(self):
        cache.clear()

    # PENGUJIAN LOGIN STAF

    def test_tc_sqli_01_login_bypass(self):
        """TC-SQLi-01: Memastikan login tidak bisa di-bypass dengan payload SQLi"""
        response = self.client.post(
            self.staff_login_url,
            {
                "username": "' OR '1'='1' --",
                "password": "bebas",
                "access_code": "TEST_DOSEN_CODE",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kredensial atau kode akses salah.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_dosen_can_use_staff_login(self):
        response = self.client.post(
            self.staff_login_url,
            {
                "username": "dosen_uji",
                "password": "passwordKuat123",
                "access_code": "TEST_DOSEN_CODE",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_asdos_can_use_staff_login(self):
        response = self.client.post(
            self.staff_login_url,
            {
                "username": "asdos_uji",
                "password": "passwordKuat123",
                "access_code": "TEST_ASDOS_CODE",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_portal_isolation_mahasiswa_cannot_use_staff_login(self):
        """Mahasiswa tidak boleh masuk lewat portal staf walau tahu kode aksesnya"""
        response = self.client.post(
            self.staff_login_url,
            {
                "username": "mhs_uji",
                "password": "passwordKuat123",
                "access_code": "TEST_DOSEN_CODE",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kredensial atau kode akses salah.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_staff_login_rejects_invalid_access_code(self):
        response = self.client.post(
            self.staff_login_url,
            {
                "username": "dosen_uji",
                "password": "passwordKuat123",
                "access_code": "KODE_SALAH",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kode akses staf tidak valid.")

    def test_tc_ba_02_staff_rate_limiting(self):
        """TC-BA-02: Portal staf terkunci setelah 5x gagal login"""
        for i in range(5):
            self.client.post(
                self.staff_login_url,
                {
                    "username": "dosen_uji",
                    "password": "passwordSalah",
                    "access_code": "KODE_SALAH",
                },
            )

        response_locked = self.client.post(
            self.staff_login_url,
            {
                "username": "dosen_uji",
                "password": "passwordKuat123",
                "access_code": "TEST_DOSEN_CODE",
            },
        )
        self.assertEqual(response_locked.status_code, 200)
        self.assertContains(
            response_locked, "Akun terkunci sementara karena 5x percobaan gagal"
        )

    def test_staff_login_view_configuration(self):
        response = self.client.get(self.staff_login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/staff_login.html")
        self.assertEqual(
            views.StaffLoginView.template_name, "accounts/staff_login.html"
        )
        self.assertIs(views.StaffLoginView.form_class, views.StaffAuthenticationForm)

    # PENGUJIAN REGISTRASI STAF

    def test_staff_register_view_get_renders_form(self):
        response = self.client.get(self.staff_register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kode Akses Staf")

    def test_staff_registration_with_dosen_code_sets_dosen_role(self):
        response = self.client.post(
            self.staff_register_url,
            {
                "username": "dosen_baru",
                "email": "dosen_baru@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": "TEST_DOSEN_CODE",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(username="dosen_baru")
        self.assertEqual(user.role, "dosen")

    def test_staff_registration_with_asdos_code_sets_asdos_role(self):
        response = self.client.post(
            self.staff_register_url,
            {
                "username": "asdos_baru",
                "email": "asdos_baru@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": "TEST_ASDOS_CODE",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(username="asdos_baru")
        self.assertEqual(user.role, "asisten_dosen")

    def test_staff_registration_rejects_invalid_access_code(self):
        response = self.client.post(
            self.staff_register_url,
            {
                "username": "staf_invalid",
                "email": "staf_invalid@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": "KODE_TIDAK_VALID",
            },
        )
        self.assertContains(response, "Kode akses tidak valid atau tidak dikenali.")

    def test_staff_registration_form_save_commit_false(self):
        form = StaffRegistrationForm(
            data={
                "username": "asdos_commit_false",
                "email": "asdos_commit_false@ui.ac.id",
                "password1": "passwordKuat123",
                "password2": "passwordKuat123",
                "access_code": "TEST_ASDOS_CODE",
            }
        )
        self.assertTrue(form.is_valid())
        user = form.save(commit=False)
        self.assertEqual(user.role, "asisten_dosen")
        self.assertIsNone(user.pk)

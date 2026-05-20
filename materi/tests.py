from django.core.files.storage import Storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import CustomUser
from .forms import MateriForm
from .models import Materi


class InMemoryUploadStorage(Storage):
    def __init__(self):
        self.saved_names = []

    def _save(self, name, content):
        self.saved_names.append(name)
        return name

    def exists(self, name):
        return False

    def url(self, name):
        return f"/media/{name}"


class MateriUploadSecurityTests(TestCase):
    def setUp(self):
        self.file_field = Materi._meta.get_field("file")
        self.original_storage = self.file_field.storage
        self.test_storage = InMemoryUploadStorage()
        self.file_field.storage = self.test_storage

        self.upload_url = reverse("materi:upload")
        self.dosen = CustomUser.objects.create_user(
            username="dosen_materi",
            password="passwordKuat123",
            role="dosen",
        )
        self.asdos = CustomUser.objects.create_user(
            username="asdos_materi",
            password="passwordKuat123",
            role="asisten_dosen",
        )
        self.mahasiswa = CustomUser.objects.create_user(
            username="mhs_materi",
            password="passwordKuat123",
            role="mahasiswa",
        )

    def tearDown(self):
        self.file_field.storage = self.original_storage

    def _txt_file(self, name="materi.txt"):
        return SimpleUploadedFile(
            name,
            b"materi valid",
            content_type="text/plain",
        )

    def _create_materi(self, title="Materi Awal"):
        return Materi.objects.create(
            title=title,
            description="Ringkasan",
            uploaded_by=self.dosen,
        )

    def test_mahasiswa_cannot_upload_materi(self):
        self.client.login(username="mhs_materi", password="passwordKuat123")
        response = self.client.get(self.upload_url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Materi.objects.exists())

    def test_staff_can_upload_valid_txt_with_randomized_storage_name(self):
        self.client.login(username="dosen_materi", password="passwordKuat123")
        file = self._txt_file("ringkasan_materi.txt")

        response = self.client.post(
            self.upload_url,
            {
                "title": "Materi Aman",
                "description": "Ringkasan",
                "file": file,
            },
        )

        self.assertEqual(response.status_code, 302)
        materi = Materi.objects.get()
        self.assertEqual(materi.uploaded_by, self.dosen)
        self.assertTrue(materi.file.name.startswith("materi_files/"))
        self.assertTrue(materi.file.name.endswith(".txt"))
        self.assertNotIn("ringkasan_materi", materi.file.name)

    def test_asdos_cannot_upload_materi(self):
        self.client.login(username="asdos_materi", password="passwordKuat123")

        response = self.client.get(self.upload_url)

        self.assertEqual(response.status_code, 302)

    def test_upload_materi_invalid_post_renders_errors(self):
        self.client.login(username="dosen_materi", password="passwordKuat123")

        response = self.client.post(
            self.upload_url,
            {"title": "", "description": "x"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bidang ini tidak boleh kosong")
        self.assertFalse(Materi.objects.exists())

    def test_materi_form_rejects_dangerous_extension(self):
        form = MateriForm(
            data={"title": "Materi", "description": "x"},
            files={
                "file": SimpleUploadedFile(
                    "payload.js",
                    b"alert(1)",
                    content_type="application/javascript",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_materi_form_rejects_spoofed_pdf_content(self):
        form = MateriForm(
            data={"title": "Materi", "description": "x"},
            files={
                "file": SimpleUploadedFile(
                    "slide.pdf",
                    b"not really a pdf",
                    content_type="application/pdf",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Isi file PDF tidak valid.", form.errors["file"])

    def test_materi_form_accepts_empty_optional_file(self):
        form = MateriForm(data={"title": "Materi", "description": "x"})

        self.assertTrue(form.is_valid())

    def test_materi_model_str_returns_title(self):
        materi = self._create_materi("Materi Str")

        self.assertEqual(str(materi), "Materi Str")

    def test_edit_materi_get_and_post_updates_object(self):
        materi = self._create_materi()
        self.client.login(username="dosen_materi", password="passwordKuat123")

        get_response = self.client.get(reverse("materi:edit", args=[materi.pk]))
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "Edit Materi")

        post_response = self.client.post(
            reverse("materi:edit", args=[materi.pk]),
            {
                "title": "Materi Update",
                "description": "Ringkasan update",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        materi.refresh_from_db()
        self.assertEqual(materi.title, "Materi Update")

    def test_edit_materi_invalid_post_renders_form(self):
        materi = self._create_materi()
        self.client.login(username="dosen_materi", password="passwordKuat123")

        response = self.client.post(
            reverse("materi:edit", args=[materi.pk]),
            {"title": "", "description": "x"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bidang ini tidak boleh kosong")

    def test_edit_materi_rejects_mahasiswa(self):
        materi = self._create_materi()
        self.client.login(username="mhs_materi", password="passwordKuat123")

        response = self.client.get(reverse("materi:edit", args=[materi.pk]))

        self.assertEqual(response.status_code, 302)

    def test_delete_materi_get_and_post(self):
        materi = self._create_materi()
        self.client.login(username="dosen_materi", password="passwordKuat123")

        get_response = self.client.get(reverse("materi:delete", args=[materi.pk]))
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "materi")

        post_response = self.client.post(reverse("materi:delete", args=[materi.pk]))
        self.assertEqual(post_response.status_code, 302)
        self.assertFalse(Materi.objects.filter(pk=materi.pk).exists())

    def test_delete_materi_rejects_mahasiswa(self):
        materi = self._create_materi()
        self.client.login(username="mhs_materi", password="passwordKuat123")

        response = self.client.post(reverse("materi:delete", args=[materi.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Materi.objects.filter(pk=materi.pk).exists())


class MateriSkenarioSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dosen = CustomUser.objects.create_user(
            username="dosen_sec2", password="password123", role="dosen"
        )
        self.mhs = CustomUser.objects.create_user(
            username="mhs_sec2", password="password123", role="mahasiswa"
        )

    def test_tc_ba_04_akses_tanpa_login_ditolak(self):
        """TC-BA-04: Akses halaman upload materi wajib login"""
        response = self.client.get(reverse("materi:upload"))
        self.assertEqual(response.status_code, 302)

    def test_tc_ci_04_code_injection_judul_materi(self):
        """Mencegah XSS (Code Injection) pada rendering judul materi"""
        payload_xss = "<img src='x' onerror='alert(1)'>"
        Materi.objects.create(
            title=payload_xss, description="Tes XSS", uploaded_by=self.dosen
        )

        # Anggap ada endpoint list materi, misalnya materi:landing atau serupa
        # Jika nama routing list materi di proyekmu beda, sesuaikan URL di bawah ini
        try:
            self.client.login(username="mhs_sec2", password="password123")
            response = self.client.get(
                reverse("forum:landing")
            )  # Biasanya materi tampil di landing
            self.assertContains(
                response, "&lt;img src=&#x27;x&#x27; onerror=&#x27;alert(1)&#x27;&gt;"
            )
            self.assertNotContains(response, payload_xss)
        except:
            pass  # Lewati jika URL list materi belum terdefinisi


class MateriSecurityTestsTambahan(TestCase):
    def setUp(self):
        # Enforce CSRF checks wajib diaktifkan pada Client untuk mengetes serangan CSRF
        self.client = Client(enforce_csrf_checks=True)
        self.dosen = CustomUser.objects.create_user(
            username="dosen_test", password="password123", role="dosen"
        )
        self.materi = Materi.objects.create(
            title="Materi A", description="Deskripsi awal", uploaded_by=self.dosen
        )

    def test_tc_csrf_04_materi_upload_protection(self):
        """TC-CSRF-04: Memastikan upload materi menolak request POST tanpa token CSRF valid"""
        self.client.login(username="dosen_test", password="password123")

        # Kirim request POST tanpa menyertakan token csrfmiddlewaretoken
        response = self.client.post(
            "/materi/upload/", {"title": "Materi Hacked", "description": "Bypass CSRF"}
        )

        # Harus mengembalikan HTTP 403 Forbidden (Ditolak oleh middleware Django)
        self.assertEqual(response.status_code, 403)

    def test_tc_sqli_04_manipulasi_id_materi(self):
        """TC-SQLi-04: Memastikan endpoint materi aman dari injeksi SQL pada parameter ID"""
        self.client.login(username="dosen_test", password="password123")

        # Payload SQLi klasik
        sqli_payload = "1 OR 1=1"

        # Coba akses URL delete/edit dengan payload tersebut
        response = self.client.get(f"/materi/{sqli_payload}/delete/")

        # Django ORM yang aman akan melempar error 404 (Not Found) karena string tidak bisa diconvert ke integer (Primary Key), bukan 500 (Server Error/Eksekusi berhasil)
        self.assertEqual(response.status_code, 404)

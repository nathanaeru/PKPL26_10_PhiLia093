from django.core.files.storage import Storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from elearning.upload_security import (
    secure_materi_upload_path,
    secure_tugas_upload_path,
    secure_upload_path,
    validate_secure_uploaded_file,
)
from .forms import SubmissionForm, TugasForm
from .models import Nilai, Submission, Tugas


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


class TugasUploadSecurityTests(TestCase):
    def setUp(self):
        self.file_field = Tugas._meta.get_field("file")
        self.original_storage = self.file_field.storage
        self.test_storage = InMemoryUploadStorage()
        self.file_field.storage = self.test_storage
        self.submission_file_field = Submission._meta.get_field("file")
        self.original_submission_storage = self.submission_file_field.storage
        self.submission_file_field.storage = InMemoryUploadStorage()

        self.upload_url = reverse("assignment:upload")
        self.dosen = CustomUser.objects.create_user(
            username="dosen_upload",
            password="passwordKuat123",
            role="dosen",
        )
        self.asdos = CustomUser.objects.create_user(
            username="asdos_upload",
            password="passwordKuat123",
            role="asisten_dosen",
        )
        self.mahasiswa = CustomUser.objects.create_user(
            username="mhs_upload",
            password="passwordKuat123",
            role="mahasiswa",
        )

    def tearDown(self):
        self.file_field.storage = self.original_storage
        self.submission_file_field.storage = self.original_submission_storage

    def _pdf_file(self, name="file.pdf"):
        return SimpleUploadedFile(
            name,
            b"%PDF-1.4\nvalid pdf",
            content_type="application/pdf",
        )

    def _txt_file(self, name="jawaban.txt"):
        return SimpleUploadedFile(
            name,
            b"jawaban valid",
            content_type="text/plain",
        )

    def _create_tugas(self, title="Tugas Awal"):
        return Tugas.objects.create(
            title=title,
            description="Deskripsi",
            uploaded_by=self.dosen,
        )

    def test_mahasiswa_cannot_upload_tugas(self):
        self.client.login(username="mhs_upload", password="passwordKuat123")
        response = self.client.get(self.upload_url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Tugas.objects.exists())

    def test_staff_can_upload_valid_pdf_with_randomized_storage_name(self):
        self.client.login(username="dosen_upload", password="passwordKuat123")
        file = self._pdf_file("instruksi_tugas.pdf")

        response = self.client.post(
            self.upload_url,
            {
                "title": "Tugas Aman",
                "description": "Instruksi",
                "deadline": "2026-05-07T10:00",
                "file": file,
            },
        )

        self.assertEqual(response.status_code, 302)
        tugas = Tugas.objects.get()
        self.assertEqual(tugas.uploaded_by, self.dosen)
        self.assertTrue(tugas.file.name.startswith("tugas_files/"))
        self.assertTrue(tugas.file.name.endswith(".pdf"))
        self.assertNotIn("instruksi_tugas", tugas.file.name)

    def test_asdos_get_upload_tugas_form(self):
        self.client.login(username="asdos_upload", password="passwordKuat123")
        response = self.client.get(self.upload_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "assignment/upload.html")

    def test_upload_tugas_invalid_post_renders_errors(self):
        self.client.login(username="dosen_upload", password="passwordKuat123")
        response = self.client.post(
            self.upload_url,
            {"title": "", "description": "x"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bidang ini tidak boleh kosong")
        self.assertFalse(Tugas.objects.exists())

    def test_tugas_form_rejects_dangerous_extension(self):
        form = TugasForm(
            data={"title": "Tugas", "description": "x"},
            files={
                "file": SimpleUploadedFile(
                    "shell.php",
                    b"<?php echo 'x';",
                    content_type="application/x-php",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_tugas_form_rejects_spoofed_pdf_content(self):
        form = TugasForm(
            data={"title": "Tugas", "description": "x"},
            files={
                "file": SimpleUploadedFile(
                    "materi.pdf",
                    b"<script>alert(1)</script>",
                    content_type="application/pdf",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Isi file PDF tidak valid.", form.errors["file"])

    def test_tugas_form_rejects_oversized_file(self):
        oversized = b"%PDF-1.4\n" + (b"0" * (5 * 1024 * 1024 + 1))
        form = TugasForm(
            data={"title": "Tugas", "description": "x"},
            files={
                "file": SimpleUploadedFile(
                    "besar.pdf",
                    oversized,
                    content_type="application/pdf",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Ukuran file maksimal 5 MB.", form.errors["file"])

    def test_tugas_form_accepts_empty_optional_file(self):
        form = TugasForm(data={"title": "Tugas", "description": "x"})

        self.assertTrue(form.is_valid())

    def test_submission_form_requires_file(self):
        form = SubmissionForm(data={})

        self.assertFalse(form.is_valid())
        self.assertIn("File submisi wajib diunggah.", form.errors["file"])

    def test_submission_form_rejects_bad_extension(self):
        form = SubmissionForm(
            files={
                "file": SimpleUploadedFile(
                    "payload.exe",
                    b"bad",
                    content_type="application/octet-stream",
                )
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("tidak diizinkan", form.errors["file"][0])

    def test_submission_form_rejects_oversized_file(self):
        form = SubmissionForm(
            files={
                "file": SimpleUploadedFile(
                    "besar.txt",
                    b"0" * (10 * 1024 * 1024 + 1),
                    content_type="text/plain",
                )
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Ukuran file melebihi batas maksimum", form.errors["file"][0])

    def test_submission_form_accepts_valid_file(self):
        form = SubmissionForm(files={"file": self._txt_file()})

        self.assertTrue(form.is_valid())

    def test_assignment_model_str_methods(self):
        tugas = self._create_tugas("Tugas Str")
        submission = Submission.objects.create(tugas=tugas, student=self.mahasiswa)
        nilai = Nilai.objects.create(
            submission=submission,
            penilai=self.dosen,
            nilai_angka=88,
            feedback="Baik",
        )

        self.assertEqual(str(tugas), "Tugas Str")
        self.assertEqual(str(submission), "mhs_upload - Tugas Str")
        self.assertEqual(str(nilai), "Nilai mhs_upload - 88")

    def test_secure_upload_path_helpers_generate_random_paths(self):
        generic_path = secure_upload_path("folder")(None, "Nama File.PDF")
        tugas_path = secure_tugas_upload_path(None, "tugas.PDF")
        materi_path = secure_materi_upload_path(None, "materi.TXT")

        self.assertTrue(generic_path.startswith("folder\\") or generic_path.startswith("folder/"))
        self.assertTrue(generic_path.endswith(".pdf"))
        self.assertTrue(tugas_path.startswith("tugas_files\\") or tugas_path.startswith("tugas_files/"))
        self.assertTrue(tugas_path.endswith(".pdf"))
        self.assertTrue(materi_path.startswith("materi_files\\") or materi_path.startswith("materi_files/"))
        self.assertTrue(materi_path.endswith(".txt"))
        self.assertNotIn("Nama File", generic_path)

    def test_secure_upload_validator_returns_for_empty_file(self):
        self.assertIsNone(validate_secure_uploaded_file(None))

    def test_secure_upload_validator_rejects_bad_content_type(self):
        file = SimpleUploadedFile(
            "valid.pdf",
            b"%PDF-1.4\nvalid",
            content_type="text/html",
        )

        with self.assertRaisesMessage(ValidationError, "Content-Type file tidak diizinkan."):
            validate_secure_uploaded_file(file)

    def test_secure_upload_validator_rejects_invalid_docx_magic_bytes(self):
        file = SimpleUploadedFile(
            "dokumen.docx",
            b"not zip",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        with self.assertRaisesMessage(ValidationError, "Isi file arsip Office/ZIP tidak valid."):
            validate_secure_uploaded_file(file)

    def test_secure_upload_validator_accepts_valid_docx_zip_and_pptx(self):
        for filename, content_type in [
            (
                "dokumen.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            ("arsip.zip", "application/zip"),
            (
                "slide.pptx",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
        ]:
            with self.subTest(filename=filename):
                file = SimpleUploadedFile(filename, b"PK\x03\x04data", content_type=content_type)
                self.assertIsNone(validate_secure_uploaded_file(file))

    def test_secure_upload_validator_rejects_invalid_legacy_office_magic_bytes(self):
        file = SimpleUploadedFile(
            "dokumen.doc",
            b"bad file",
            content_type="application/msword",
        )

        with self.assertRaisesMessage(ValidationError, "Isi file Office lama tidak valid."):
            validate_secure_uploaded_file(file)

    def test_secure_upload_validator_accepts_valid_legacy_office_files(self):
        header = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
        for filename, content_type in [
            ("dokumen.doc", "application/msword"),
            ("slide.ppt", "application/vnd.ms-powerpoint"),
        ]:
            with self.subTest(filename=filename):
                file = SimpleUploadedFile(filename, header + b"data", content_type=content_type)
                self.assertIsNone(validate_secure_uploaded_file(file))

    def test_secure_upload_validator_rejects_non_utf8_txt(self):
        file = SimpleUploadedFile(
            "catatan.txt",
            b"\xff\xfe\xfa",
            content_type="text/plain",
        )

        with self.assertRaisesMessage(ValidationError, "Isi file TXT harus berupa teks UTF-8."):
            validate_secure_uploaded_file(file)

    def test_edit_tugas_get_and_post_updates_object(self):
        tugas = self._create_tugas()
        self.client.login(username="dosen_upload", password="passwordKuat123")

        get_response = self.client.get(reverse("assignment:edit", args=[tugas.pk]))
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "Edit Tugas")

        post_response = self.client.post(
            reverse("assignment:edit", args=[tugas.pk]),
            {
                "title": "Tugas Update",
                "description": "Deskripsi update",
                "deadline": "2026-05-08T09:00",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        tugas.refresh_from_db()
        self.assertEqual(tugas.title, "Tugas Update")

    def test_edit_tugas_rejects_mahasiswa(self):
        tugas = self._create_tugas()
        self.client.login(username="mhs_upload", password="passwordKuat123")

        response = self.client.get(reverse("assignment:edit", args=[tugas.pk]))

        self.assertEqual(response.status_code, 302)

    def test_delete_tugas_get_and_post(self):
        tugas = self._create_tugas()
        self.client.login(username="dosen_upload", password="passwordKuat123")

        get_response = self.client.get(reverse("assignment:delete", args=[tugas.pk]))
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "tugas")

        post_response = self.client.post(reverse("assignment:delete", args=[tugas.pk]))
        self.assertEqual(post_response.status_code, 302)
        self.assertFalse(Tugas.objects.filter(pk=tugas.pk).exists())

    def test_delete_tugas_rejects_mahasiswa(self):
        tugas = self._create_tugas()
        self.client.login(username="mhs_upload", password="passwordKuat123")

        response = self.client.post(reverse("assignment:delete", args=[tugas.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tugas.objects.filter(pk=tugas.pk).exists())

    def test_daftar_tugas_and_daftar_submission_render(self):
        tugas = self._create_tugas()
        Submission.objects.create(tugas=tugas, student=self.mahasiswa)
        self.client.login(username="dosen_upload", password="passwordKuat123")

        tugas_response = self.client.get(reverse("assignment:daftar_tugas"))
        submission_response = self.client.get(
            reverse("assignment:daftar_submission", args=[tugas.pk])
        )

        self.assertEqual(tugas_response.status_code, 200)
        self.assertEqual(submission_response.status_code, 200)
        self.assertContains(submission_response, tugas.title)

    def test_beri_nilai_forbidden_for_mahasiswa(self):
        tugas = self._create_tugas()
        submission = Submission.objects.create(tugas=tugas, student=self.mahasiswa)
        self.client.login(username="mhs_upload", password="passwordKuat123")

        response = self.client.get(reverse("assignment:beri_nilai", args=[submission.pk]))

        self.assertEqual(response.status_code, 403)

    def test_beri_nilai_get_and_post_creates_nilai(self):
        tugas = self._create_tugas()
        submission = Submission.objects.create(tugas=tugas, student=self.mahasiswa)
        self.client.login(username="dosen_upload", password="passwordKuat123")

        get_response = self.client.get(reverse("assignment:beri_nilai", args=[submission.pk]))
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(
            reverse("assignment:beri_nilai", args=[submission.pk]),
            {"nilai": "90", "feedback": "Bagus"},
        )

        self.assertEqual(post_response.status_code, 302)
        nilai = Nilai.objects.get(submission=submission)
        self.assertEqual(nilai.nilai_angka, 90)
        self.assertEqual(nilai.feedback, "Bagus")

    def test_beri_nilai_get_existing_nilai(self):
        tugas = self._create_tugas()
        submission = Submission.objects.create(tugas=tugas, student=self.mahasiswa)
        Nilai.objects.create(
            submission=submission,
            penilai=self.dosen,
            nilai_angka=80,
            feedback="OK",
        )
        self.client.login(username="dosen_upload", password="passwordKuat123")

        response = self.client.get(reverse("assignment:beri_nilai", args=[submission.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "80")

    def test_submission_status_rejects_staff_and_renders_for_student(self):
        tugas = self._create_tugas()
        self.client.login(username="dosen_upload", password="passwordKuat123")
        staff_response = self.client.get(
            reverse("assignment:submission_status", args=[tugas.pk])
        )
        self.assertEqual(staff_response.status_code, 302)

        self.client.login(username="mhs_upload", password="passwordKuat123")
        student_response = self.client.get(
            reverse("assignment:submission_status", args=[tugas.pk])
        )
        self.assertEqual(student_response.status_code, 200)

    def test_submission_status_includes_existing_nilai(self):
        tugas = self._create_tugas()
        submission = Submission.objects.create(tugas=tugas, student=self.mahasiswa)
        Nilai.objects.create(
            submission=submission,
            penilai=self.dosen,
            nilai_angka=85,
            feedback="Mantap",
        )
        self.client.login(username="mhs_upload", password="passwordKuat123")

        response = self.client.get(reverse("assignment:submission_status", args=[tugas.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "85")

    def test_submission_status_handles_submission_without_nilai(self):
        tugas = self._create_tugas()
        Submission.objects.create(tugas=tugas, student=self.mahasiswa)
        self.client.login(username="mhs_upload", password="passwordKuat123")

        response = self.client.get(reverse("assignment:submission_status", args=[tugas.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tugas.title)

    def test_upload_submisi_rejects_staff(self):
        tugas = self._create_tugas()
        self.client.login(username="dosen_upload", password="passwordKuat123")

        response = self.client.get(reverse("assignment:upload_submisi", args=[tugas.pk]))

        self.assertEqual(response.status_code, 302)

    def test_upload_submisi_get_create_update_and_invalid_post(self):
        tugas = self._create_tugas()
        self.client.login(username="mhs_upload", password="passwordKuat123")

        get_response = self.client.get(reverse("assignment:upload_submisi", args=[tugas.pk]))
        self.assertEqual(get_response.status_code, 200)

        invalid_response = self.client.post(
            reverse("assignment:upload_submisi", args=[tugas.pk]),
            {},
        )
        self.assertEqual(invalid_response.status_code, 200)

        create_response = self.client.post(
            reverse("assignment:upload_submisi", args=[tugas.pk]),
            {"file": self._txt_file("jawaban.txt")},
        )
        self.assertEqual(create_response.status_code, 302)
        submission = Submission.objects.get(tugas=tugas, student=self.mahasiswa)
        self.assertTrue(submission.file.name.startswith("submission_files/"))

        update_response = self.client.post(
            reverse("assignment:upload_submisi", args=[tugas.pk]),
            {"file": self._txt_file("jawaban_baru.txt")},
        )
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(Submission.objects.filter(tugas=tugas, student=self.mahasiswa).count(), 1)

    def test_delete_submisi_rejects_staff_and_deletes_for_owner(self):
        tugas = self._create_tugas()
        submission = Submission.objects.create(tugas=tugas, student=self.mahasiswa)

        self.client.login(username="dosen_upload", password="passwordKuat123")
        staff_response = self.client.get(reverse("assignment:delete_submisi", args=[tugas.pk]))
        self.assertEqual(staff_response.status_code, 302)

        self.client.login(username="mhs_upload", password="passwordKuat123")
        get_response = self.client.get(reverse("assignment:delete_submisi", args=[tugas.pk]))
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(reverse("assignment:delete_submisi", args=[tugas.pk]))
        self.assertEqual(post_response.status_code, 302)
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())

import os
import random
import tempfile
from django.core.management.base import BaseCommand
from django.core.files import File
from accounts.models import CustomUser  # Menggunakan CustomUser
from assignment.models import Tugas, Submission, Nilai
from materi.models import Materi
from forum.models import Post
from faker import Faker
from fpdf import FPDF


def generate_dummy_pdf(filename, title, content_lines=5, fake_instance=None):
    """Menghasilkan file PDF sederhana di direktori temporary yang aman untuk semua OS."""
    if fake_instance is None:
        fake_instance = Faker("id_ID")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(10)

    for _ in range(content_lines):
        pdf.multi_cell(0, 10, txt=fake_instance.paragraph(nb_sentences=5))
        pdf.ln(5)

    # Gunakan tempfile.gettempdir() agar menyesuaikan dengan OS (Windows/Linux/Mac)
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, filename)

    pdf.output(temp_path)
    return temp_path


class Command(BaseCommand):
    help = "Seed database dengan data dummy lengkap sesuai model (User, Forum, Materi, Tugas, Submission)"

    def handle(self, *args, **kwargs):
        fake = Faker("id_ID")

        self.stdout.write("Mulai generate Users...")
        users_created = {"dosen": [], "asisten_dosen": [], "mahasiswa": []}

        # 1. Generate Dosen
        for i in range(2):
            user = CustomUser.objects.create_user(
                username=f"dosen{i+1}",
                email=fake.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role="dosen",  # Sesuai ROLE_CHOICES
            )
            users_created["dosen"].append(user)

        # 2. Generate Asisten Dosen
        for i in range(3):
            user = CustomUser.objects.create_user(
                username=f"asdos{i+1}",
                email=fake.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role="asisten_dosen",  # Sesuai ROLE_CHOICES
            )
            users_created["asisten_dosen"].append(user)

        # 3. Generate Mahasiswa
        for i in range(10):
            user = CustomUser.objects.create_user(
                username=f"mhs{i+1}",
                email=fake.email(),
                password="password123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role="mahasiswa",  # Sesuai ROLE_CHOICES
            )
            users_created["mahasiswa"].append(user)

        self.stdout.write(self.style.SUCCESS("Berhasil membuat data User!"))

        # --- SEEDING MATERI ---
        self.stdout.write("Mulai generate Materi...")
        for i in range(3):
            judul_materi = f"Materi {i+1}: {fake.catch_phrase()}"
            pdf_path = generate_dummy_pdf(
                f"materi_{i}.pdf", judul_materi, fake_instance=fake
            )

            materi = Materi(
                title=judul_materi,
                description=fake.text(),
                uploaded_by=random.choice(
                    users_created["dosen"]
                ),  # Atribut sesuai model
            )
            with open(pdf_path, "rb") as f:
                materi.file.save(f"materi_{i}.pdf", File(f))
            materi.save()
            os.remove(pdf_path)

        # --- SEEDING TUGAS & SUBMISSION ---
        self.stdout.write("Mulai generate Tugas & Submission...")
        for i in range(2):
            judul_tugas = f"Tugas {i+1}: {fake.bs()}"
            pdf_path_tugas = generate_dummy_pdf(
                f"soal_tugas_{i}.pdf", judul_tugas, fake_instance=fake
            )

            tugas = Tugas(
                title=judul_tugas,
                description=fake.text(),
                uploaded_by=random.choice(
                    users_created["dosen"]
                ),  # Atribut sesuai model
            )
            with open(pdf_path_tugas, "rb") as f:
                tugas.file.save(f"soal_tugas_{i}.pdf", File(f))
            tugas.save()
            os.remove(pdf_path_tugas)

            # Mahasiswa mengerjakan tugas
            for mhs in random.sample(
                users_created["mahasiswa"], 5
            ):  # 5 mahasiswa acak kumpulkan tugas
                pdf_path_submisi = generate_dummy_pdf(
                    f"jawaban_{mhs.username}_{i}.pdf",
                    f"Jawaban {judul_tugas}",
                    fake_instance=fake,
                )
                submission = Submission(
                    tugas=tugas, student=mhs  # Atribut sesuai model
                )
                with open(pdf_path_submisi, "rb") as f:
                    submission.file.save(f"jawaban_{mhs.username}_{i}.pdf", File(f))
                submission.save()
                os.remove(pdf_path_submisi)

                # Opsional: Beri nilai untuk beberapa submission oleh asdos
                Nilai.objects.create(
                    submission=submission,
                    penilai=random.choice(users_created["asisten_dosen"]),
                    nilai_angka=random.randint(60, 100),
                    feedback=fake.sentence(),
                )

        # --- SEEDING FORUM ---
        self.stdout.write("Mulai generate data Forum...")
        all_users = (
            users_created["dosen"]
            + users_created["asisten_dosen"]
            + users_created["mahasiswa"]
        )

        for _ in range(5):
            thread = Post.objects.create(
                title=fake.sentence(nb_words=6),
                content=fake.paragraph(nb_sentences=4),
                author=random.choice(all_users),
                parent=None,
            )

            for _ in range(random.randint(1, 4)):
                Post.objects.create(
                    title=f"Re: {thread.title}",  # Opsional, biasanya null untuk reply, tapi kita isi biar aman
                    content=fake.paragraph(nb_sentences=2),
                    author=random.choice(all_users),
                    parent=thread,
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Seluruh data seeding (User, Materi, Tugas, Forum) berhasil ditambahkan!"
            )
        )

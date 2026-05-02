# Tugas 3: Secure Coding Implementation

## Kelas: PKPL C

## Nama Kelompok: PhiLia093

**Anggota Kelompok:**

- Nathanael Leander Herdanatra (2406421320)
- Raihana Nur Azizah (2406413426)
- Rochelle Marchia Arisandi (2406429014)
- Dibrienna Rauseuky (2406429834)
- Ardyana Feby Pratiwi (2406398274)

## Cara Menjalankan Proyek

Persyaratan: Versi Python 3.12+

1. Clone repository ini.

2. Navigasi ke direktori proyek dan buat lingkungan virtual (virtual environment):

    **Untuk Windows:**

    ```powershell
    python -m venv env
    ```

    **Untuk Unix/Linux atau MacOS:**

    ```bash
    python3 -m venv env
    ```

3. Aktifkan lingkungan virtual:

    **Untuk Windows:**

    ```powershell
     env\Scripts\activate
    ```

    **Untuk Unix/Linux atau MacOS:**

    ```bash
    source env/bin/activate
    ```

4. Instal dependensi yang diperlukan:

    ```bash
    pip install -r requirements.txt
    ```

5. Copy file `.env.example` menjadi `.env` dan isi dengan konfigurasi yang sesuai (seperti kunci untuk akses registrasi dosen dan asdos, secret key, dan debug mode). Untuk secret key merupakan string 50 karakter random, dapat di-generate dari [sini](https://djecrety.ir/).

6. Migrasi database:
    ```bash
    python manage.py migrate
    ```
7. Jalankan server development:
    ```bash
    python manage.py runserver
    ```
8. Buka URL localhost yang disediakan di terminal (biasanya http://127.0.0.1:8000) di browser web Anda untuk melihat aplikasi berjalan.

## Cara Registrasi dan Login sebagai Staff (Dosen/Asisten Dosen)

Untuk keamanan, login untuk staf (dosen dan asisten dosen) memerlukan kode akses khusus yang harus dimasukkan saat login, dan URL ini hanya dapat diakses melalui akses langsung di browser (tidak di-link dari halaman lain). Berikut langkah-langkahnya:

1. Pastikan Anda sudah memiliki akun staf yang terdaftar. Jika belum, Anda dapat mendaftar melalui halaman registrasi staf di URL: http://localhost:8000/accounts/portal-register-staff/. Saat registrasi, Anda akan diminta untuk memasukkan kode akses yang sesuai (kode akses untuk dosen atau asisten dosen). Kode ini terletak di file `.env` sebagai `DOSEN_CODE` untuk dosen dan `ASDOS_CODE` untuk asisten dosen.
2. Setelah berhasil mendaftar, Anda dapat login melalui halaman login staf di URL: http://localhost:8000/accounts/portal-login-staff/. Di halaman login ini, selain memasukkan username dan password, Anda juga harus memasukkan kode akses yang sesuai dengan peran Anda (dosen atau asisten dosen).

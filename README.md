# Tugas 3: Secure Coding Implementation

### Kelas: PKPL C

### Nama Kelompok: PhiLia093

**Anggota Kelompok:**

- Nathanael Leander Herdanatra (2406421320)
- Raihana Nur Azizah (2406413426)
- Rochelle Marchia Arisandi (2406429014)
- Dibrienna Rauseuky (2406429834)
- Ardyana Feby Pratiwi (2406398274)

### How to Run the Project

Requirement: Python version 3.12+

1. Clone this repo.

2. Navigate to the project directory and create a virtual environment:

    **For Windows:**

    ```powershell
    python -m venv env
    ```

    **For Unix/Linux or MacOS:**

    ```bash
    python3 -m venv env
    ```

3. Activate the virtual environment:

    **For Windows:**

    ```powershell
     env\Scripts\activate
    ```

    **For Unix/Linux or MacOS:**

    ```bash
    source env/bin/activate
    ```

4. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5. Migrate the database:
    ```bash
    python manage.py migrate
    ```
6. Run the development server:
    ```bash
    python manage.py runserver
    ```
7. Open the localhost URL provided in the terminal (usually http://127.0.0.1:8000) in your web browser to see the application running.

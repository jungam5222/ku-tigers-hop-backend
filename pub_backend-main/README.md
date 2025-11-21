# Pub Backend

This is a Django-based backend project for managing reservations, tables, and orders in a pub.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (optional but recommended)

## Setup Instructions

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ku-pub/pub_backend.git
   cd pub_backend
   ```

2. **Create and Activate a Virtual Environment (Optional)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Apply Migrations**

   ```bash
   python manage.py migrate
   ```

5. **Run the Development Server**

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

6. **Access the Application**

   Open your browser and go to `http://0.0.0.0:8000`.

## Additional Notes

- **Django Version**: This project uses Django 4.2.
- **Database**: The default database is SQLite, which is suitable for development.
- **Admin Panel**: Access the admin panel at `http://0.0.0.0:8000/admin`.

## Development Tips

- To create a superuser for the admin panel, run:

  ```bash
  python manage.py createsuperuser
  ```

- If you make changes to the models, don't forget to create and apply migrations:

  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

- Use the following command to install additional dependencies:

  ```bash
  pip install <package-name>
  ```

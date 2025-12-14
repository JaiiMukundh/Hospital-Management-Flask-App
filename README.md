# Hospital Management System (MAD-I Project)

This is a web-based Hospital Management System developed for the Modern Application Development I course. It features a role-based access system for Administrators, Doctors, and Patients, built using the Flask framework in Python.



### Core Technologies Used
- **Backend:** Python, Flask
- **Database:** SQLite (with Flask-SQLAlchemy)
- **Authentication:** Flask-Login
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript
- **Forms:** Flask-WTF



### Setup and Installation Instructions

To run this project, you will need to set up a Python virtual environment and install the required packages.

**1. Prerequisites**
   - Ensure you have Python 3 installed on your system.

**2. Unzip and Navigate**
   - Unzip the project folder and open a terminal or command prompt in the root directory of the project (the folder containing `app.py`).

**3. Create the Virtual Environment**
   - Run the following command to create a new virtual environment folder named `venv`:

     **For macOS/Linux:**

     python3 -m venv venv
     ```
     **For Windows:**

     python -m venv venv

   - This will create a new folder named `venv` in your project directory.

**4. Activate the Virtual Environment**
   - You must activate the environment before installing packages.

     **For macOS/Linux:**

     source venv/bin/activate

     **For Windows:**

     venv\Scripts\activate

   - Your terminal prompt should now show `(venv)` at the beginning, indicating that the environment is active.

**5. Install Required Packages**
   - With the virtual environment active, run the following command to install all necessary dependencies:

     pip install -r requirements.txt

   - This command will read the `requirements.txt` file and install libraries like Flask, SQLAlchemy, etc., into your `venv`.


### Running the Application

1.  **Ensure your virtual environment is still active** (`(venv)` is visible in your terminal prompt).

2.  Run the following command in the root project directory:

    python app.py

3.  The application will start, and the database file (`hospital.db`) will be created automatically in an `instance` folder.

4.  Open your web browser and navigate to:

    http://127.0.0.1:5000

import os
import sys
import datetime
import time
from dotenv import load_dotenv
from scheduler import Scheduler
from flask import Flask, request, render_template
import resend
import mysql.connector
from mysql.connector import Error
from newshtml import get_content

load_dotenv()

# Set API key
resend.api_key = os.environ.get('RESEND_API_KEY')

# Initialize scheduler and app
schedule = Scheduler()
app = Flask(__name__)

# Define news URLs
news_urls = ["http://lite.cnn.com",
             "http://legiblenews.com", "http://text.npr.org"]

# Function to create a database connection


def create_connection():
    max_attempts = 5
    attempts = 0
    while attempts < max_attempts:
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST'),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
            )
            app.logger.info("%s", mysql.connector.__version__)
            break
        except Error as e:
            app.logger.error(
                "Failed to connect to MySQL: %s. Attempt %d of %d.", e, attempts + 1, max_attempts)
            attempts += 1
            time.sleep(1)  # wait for 1 second before trying again
    if conn is None:
        app.logger.error("Failed to connect to MySQL after multiple attempts.")
        sys.exit(1)
    return conn

# Function to create a database


def create_database(db_name):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    except Error as e:
        app.logger.error("Failed to create database: %s", e)

# Function to create a table


def create_table(table_name):
    try:
        cursor.execute("USE HeadlineHub")
        cursor.execute(f"""
         CREATE TABLE IF NOT EXISTS {table_name} (
             id INT AUTO_INCREMENT PRIMARY KEY,
             email VARCHAR(255) NOT NULL UNIQUE
         )
     """)
    except Error as e:
        app.logger.error("Failed to create table: %s", e)

# Command to start the database


@app.cli.command('start_db')
def start_db():
    conn = create_connection()
    if conn is not None:
        db_name = "HeadlineHub"
        table_name = "users"
        create_database(db_name)
        create_table(table_name)
    else:
        app.logger.error("Error! Cannot create the database connection.")


@app.cli.command('schedule')
def tasks():
    print(schedule)


# Create a connection and cursor
try:
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("USE HeadlineHub")
except:
    app.logger.error("Error! Cannot create the database cursor.")
    sys.exit(1)

# Function to send emails


@app.cli.command('send_email')
def send_email(urls):
    try:
        html = get_content(urls)
    except Exception as e:
        app.logger.info("Failed to get content: %s", e)
        return

    try:
        cursor.execute("SELECT email FROM users")
        rows = cursor.fetchall()
    except Error as e:
        app.logger.critical("Failed to fetch emails: %s", e)
        return

    try:
        params = {
            "from": "HeadlineHub <onboarding@resend.dev>",
            "to": list(rows),
            "subject": f"HeadlineHub for {datetime.date.today()}",
            "html": html,
        }
        email = resend.Emails.send(params)
    except Exception as e:
        app.logger.critical("Failed to send email: %s", e)
        return

    return email

# Route to add a user


@app.route("/", methods=['POST', 'GET'])
def add_user():
    if request.method == 'POST':
        try:
            add_data = ("INSERT INTO users "
                        "(email) "
                        "VALUES (%s)")

            # Data to be inserted
            data = (request.form.get("email"))

            # Execute the SQL command
            cursor.execute(add_data, data)
            conn.commit()
        except Error as e:
            app.logger.error("Failed to insert data: %s", e)
    else:
        return render_template('index.html')


# Schedule daily email sending
schedule.daily(datetime.time(hour=5, minute=30), send_email(news_urls))

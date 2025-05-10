import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pickle
import base64
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json
import google.generativeai as genai
import os
import datetime

# Use Streamlit Secrets for sensitive information
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
TO_EMAIL = st.secrets["TO_EMAIL"]
CLIENT_SECRET_JSON = st.secrets["CLIENT_SECRET_JSON"]

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use client secret JSON from Streamlit secrets
            with open("client_secret.json", "w") as f:
                f.write(CLIENT_SECRET_JSON)
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def send_email_via_gmail(subject, body, to_email):
    service = build('gmail', 'v1', credentials=authenticate_gmail())
    message = MIMEMultipart()
    message['to'] = to_email
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
    st.success("📤 Email sent successfully")


def generate_email_content(problem_title, problem_link, prev_difficulty, day_of_week, user_behavior, is_revision=False):
    if is_revision:
        prompt = f"""
You are an AI tutor sending a short motivational revision email.
Today is {day_of_week}.
The student is revisiting: "{problem_title}" (link: {problem_link}).

Write:
- A friendly greeting
- Mention it's a revision task and why it's helpful
- Encourage them to recall the key idea
- End with a motivational boost
        """
        subject = "🧠 Time to Revise a DSA Problem!"
    elif user_behavior.lower() == "skipped":
        prompt = f"""
You are an AI tutor reaching out to a student who skipped their last DSA problem.
Today is {day_of_week}.
Here’s the new opportunity: "{problem_title}" ({prev_difficulty}) - {problem_link}

Write:
- A kind, empathetic message
- Normalize skipping (everyone does it!)
- Emphasize progress over perfection
- Encourage giving this new problem a try
- Keep it short, warm, and motivational
        """
        subject = "💪 It's Okay to Skip — Let's Tackle a New DSA Problem!"
    elif user_behavior.lower() == "completed":
        prompt = f"""
You are an AI tutor congratulating a student for solving a previous DSA problem.
Today is {day_of_week}.
The next challenge is: "{problem_title}" ({prev_difficulty}) - {problem_link}

Write:
- A big congratulations
- Acknowledge their consistency
- Encourage them to keep the streak going
- Add a link to the new problem
        """
        subject = "🎉 Great Work! Ready for the Next DSA Challenge?"
    else:
        prompt = f"""
You are an AI tutor encouraging a student to continue DSA practice.
Today is {day_of_week}.
The problem for today is: "{problem_title}" ({prev_difficulty}) - {problem_link}

Write:
- A warm greeting
- Explain how today's problem fits their journey
- Motivate and guide them to keep practicing
        """
        subject = "🚀 Your Daily DSA Problem Awaits!"

    try:
        response = model.generate_content(prompt)
        return subject, response.text.strip()
    except Exception as e:
        st.error(f"⚠️ Gemini API failed: {str(e)}")
        fallback = f"Here's your problem of the day: {problem_title}\n{problem_link}"
        return subject, fallback


def create_and_send_email_from_json():
    try:
        with open("selected_problem.json", "r") as f:
            data = json.load(f)

        problem_title = data["Title"]
        problem_link = data["Leetcode Question Link"]
        prev_difficulty = data.get("Previous Difficulty", "Medium")
        user_behavior = data.get("User Behavior", "skipped")
        is_revision = "revision" in data.get("Tag", "").lower()
        day_of_week = datetime.datetime.now().strftime("%A")

        subject, email_body = generate_email_content(
            problem_title=problem_title,
            problem_link=problem_link,
            prev_difficulty=prev_difficulty,
            day_of_week=day_of_week,
            user_behavior=user_behavior,
            is_revision=is_revision
        )

        send_email_via_gmail(subject=subject, body=email_body, to_email=TO_EMAIL)

    except FileNotFoundError:
        st.error("❌ selected_problem.json not found.")
    except Exception as e:
        st.error(f"❌ Error: {e}")


if __name__ == "__main__":
    st.title("Send DSA Problem Email")
    if st.button("Send Email"):
        create_and_send_email_from_json()

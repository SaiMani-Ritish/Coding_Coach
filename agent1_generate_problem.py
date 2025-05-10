import streamlit as st
import os
import pandas as pd
import google.generativeai as genai
import json
import re
from datetime import datetime
from difflib import get_close_matches
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pickle

# Use Streamlit Secrets for sensitive information
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
TO_EMAIL = st.secrets["TO_EMAIL"]
CLIENT_SECRET_JSON = st.secrets["CLIENT_SECRET_JSON"]

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    creds = None
    token_path = 'token.pickle'
    
    try:
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Write client secrets from Streamlit secrets
                client_secret_file = "client_secret.json"
                with open(client_secret_file, "w") as f:
                    json.dump(json.loads(st.secrets["CLIENT_SECRET_JSON"]), f)
                
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Save the credentials
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                    
                # Clean up client secret file
                if os.path.exists(client_secret_file):
                    os.remove(client_secret_file)
                    
        return creds
    except Exception as e:
        st.error(f"Authentication Error: {str(e)}")
        return None

def send_email_via_gmail(subject, body, to_email):
    try:
        creds = authenticate_gmail()
        if not creds:
            st.error("Failed to authenticate with Gmail")
            return False
            
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject
        message['from'] = st.secrets.get("FROM_EMAIL", "me")
        message.attach(MIMEText(body, 'plain'))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            st.success("📤 Email sent successfully")
            return True
        except Exception as e:
            st.error(f"Failed to send email: {str(e)}")
            return False
            
    except Exception as e:
        st.error(f"Email Error: {str(e)}")
        return False

def load_problems(csv_file):
    return pd.read_csv(csv_file)

def append_to_history(new_entry, filename="all_attempts.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(new_entry)

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_problem_link_by_title(title, df):
    try:
        # Normalize both input and DataFrame titles for better matching
        title = title.lower().strip()
        df = df.copy()  # Create a copy to avoid modifying original DataFrame
        df["normalized_title"] = df["Title"].str.lower().str.strip()
        
        titles = df["normalized_title"].tolist()
        close = get_close_matches(title, titles, n=1, cutoff=0.6)
        
        if close:
            match_row = df[df["normalized_title"] == close[0]].iloc[0]
            return match_row["Leetcode Question Link"], match_row["Title"], True
        
        return "https://leetcode.com", title, False
    except Exception as e:
        st.error(f"Error matching problem title: {str(e)}")
        return "https://leetcode.com", title, False

def check_revision_needed(attempts, df):
    try:
        today = datetime.now().date()
        for attempt in attempts:
            if attempt["Completed"] == "yes":
                try:
                    date_solved = datetime.strptime(attempt["date_attempted"], "%Y-%m-%d").date()
                    days_diff = (today - date_solved).days
                    
                    if days_diff == 7:
                        link = attempt.get("Leetcode Question Link", "").strip()
                        if not link:
                            link, matched_title, found = get_problem_link_by_title(attempt["Title"], df)
                            if found:
                                attempt["Title"] = matched_title
                                attempt["Leetcode Question Link"] = link
                                st.info(f"Found revision problem: {matched_title}")
                            else:
                                st.warning(f"Could not find exact match for: {attempt['Title']}")
                        return attempt
                except ValueError as e:
                    st.warning(f"Invalid date format for attempt: {attempt['Title']}")
                    continue
        return None
    except Exception as e:
        st.error(f"Error checking revision problems: {str(e)}")
        return None

def pick_problem_with_ai(df, prev_title, prev_difficulty, recent_tags, completed, date_attempted, all_attempts):
    revision_problem = check_revision_needed(all_attempts, df)
    if revision_problem:
        return json.dumps({
            "Title": revision_problem["Title"],
            "Difficulty": revision_problem["Difficulty"],
            "Link": revision_problem.get("Leetcode Question Link", "https://leetcode.com"),
            "Reason": "This problem is due for revision as it was solved exactly 7 days ago."
        }), True

    problems_data = df[["Title", "Difficulty", "Question Type", "Leetcode Question Link"]].to_dict(orient="records")[:30]

    prompt = f"""
You are an AI tutor designed to help a student practice Data Structures and Algorithms (DSA) on LeetCode.

The student recently attempted the LeetCode problem titled **"{prev_title}"** with difficulty **{prev_difficulty}**.
Completion status: **{completed}**.
Date: {date_attempted}.

### Guidelines for Selecting the Next Problem:
- If the last problem was **Easy** and **not completed**, suggest the **same or easier**.
- If **Medium** and **not completed**, suggest an **Easy or Medium** problem.
- If **Hard** and **not completed**, suggest a **Medium**.
- If completed, increase or maintain challenge level, staying within similar or varied topics.
- Avoid repeating tags: {recent_tags}

📚 Summary of Recent Attempts:
""" + "\n".join([
        f"- {a['Title']} ({a['Difficulty']}): {'Completed' if a['Completed'] == 'yes' else 'Skipped'} on {a['date_attempted']}"
        for a in all_attempts[-5:]
    ]) + """

🎯 Return result as:
{
    "Title": "<problem title>",
    "Difficulty": "<difficulty>",
    "Link": "<Leetcode link>",
    "Reason": "<1-sentence reason>"
}
ONLY return valid JSON.
"""

    response = model.generate_content(prompt)
    return response.text, False

def save_selected_problem(problem_title, problem_link, prev_difficulty, recent_tags, user_behavior, reason, is_revision=False, completed='no'):
    data = {
        "Title": problem_title,
        "Leetcode Question Link": problem_link,
        "Previous Difficulty": prev_difficulty,
        "Recent Tags": recent_tags,
        "User Behavior": user_behavior,
        "Reason": reason
    }
    if is_revision:
        data["Tag"] = "revision"
    if completed == 'no':
        data["Tag"] = data.get("Tag", "") + " not Complete"

    with open("selected_problem.json", "w") as f:
        json.dump(data, f, indent=4)

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

st.title("Coding Coach")

# Streamlit inputs
st.header("Previous Problem Details")
previous_title = st.text_input("Enter the problem you solved previously:")
prev_difficulty = st.selectbox("Enter its difficulty:", ["Easy", "Medium", "Hard"])
time_taken = st.text_input("How much time did you take (e.g., 30 mins):")
completed = st.radio("Did you complete the problem?", ["yes", "no"])
recent_tags = st.text_input("Enter tags (comma-separated) for that problem:").split(",")
date_attempted = st.date_input("Enter the date:", datetime.now()).strftime("%Y-%m-%d")

if st.button("Save Previous Attempt"):
    previous_attempt = {
        "Title": previous_title,
        "Difficulty": prev_difficulty,
        "Time Taken": time_taken,
        "Completed": completed,
        "Tags": [tag.strip() for tag in recent_tags],
        "date_attempted": date_attempted
    }

    append_to_history(previous_attempt)
    st.success("📝 Saved previous attempt.")

    with open("all_attempts.json", "r") as f:
        all_attempts = json.load(f)

    df = load_problems("leetcode_question.csv")

    ai_response, is_revision = pick_problem_with_ai(
        df,
        prev_title=previous_attempt["Title"],
        prev_difficulty=previous_attempt["Difficulty"],
        recent_tags=previous_attempt["Tags"],
        completed=previous_attempt["Completed"],
        date_attempted=previous_attempt["date_attempted"],
        all_attempts=all_attempts
    )

    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            raise ValueError("No valid JSON found.")

        problem_title = parsed["Title"]
        problem_link = parsed["Link"]
        reason = parsed["Reason"]
        user_behavior = "skipped" if previous_attempt["Completed"] == "no" else "completed"

        save_selected_problem(
            problem_title,
            problem_link,
            previous_attempt["Difficulty"],
            previous_attempt["Tags"],
            user_behavior,
            reason,
            is_revision,
            completed
        )

        st.success("✅ Problem selected and saved to JSON")
        st.json(parsed)

        if st.button("Send Email"):
            day_of_week = datetime.now().strftime("%A")
            subject, email_body = generate_email_content(
                problem_title=problem_title,
                problem_link=problem_link,
                prev_difficulty=previous_attempt["Difficulty"],
                day_of_week=day_of_week,
                user_behavior=user_behavior,
                is_revision=is_revision
            )
            if not send_email_via_gmail(subject=subject, body=email_body, to_email=TO_EMAIL):
                st.error("Please check your Gmail authentication settings in Streamlit secrets")

    except Exception as e:
        st.error(f"❌ Failed to parse AI response: {str(e)}")
        st.text("Raw response:")
        st.text(ai_response)

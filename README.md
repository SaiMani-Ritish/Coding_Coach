# Coding Coach: Your Personalized Leet Code Companion

Welcome to Coding Coach! This Python application is designed to help you level up your coding skills through personalized problem selection and intelligent revision scheduling. Leveraging the power of Google's Gemini AI and the interactivity of Streamlit, Coding Coach provides a unique and engaging learning experience.

## Features

Here's what Coding Coach can do for you:

* **Interactive Web Interface:** Enjoy a user-friendly and intuitive experience powered by Streamlit.
* **Daily Coding Challenges:** Receive a daily coding problem directly in your Gmail inbox, keeping your practice consistent.
* **Intelligent Problem Selection:** Benefit from problem recommendations powered by Google's Gemini AI, tailored to your current skill level and learning goals.
* **LeetCode History Tracking:** Seamlessly track your solved problems on LeetCode to avoid repetition and identify areas for improvement.
* **Spaced Repetition for Revision:** Revisit previously solved problems at optimal intervals to reinforce your understanding and retention.
* **Personalized Difficulty Adjustment:** The difficulty of recommended problems adapts based on your performance, ensuring continuous growth without overwhelming you.
* **Notification**

## Installation Steps

Get Coding Coach up and running in a few easy steps:

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository_url>
    cd coding-coach
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration Guide

To use all the features of Coding Coach, you'll need to configure the following:

1.  **Streamlit Secrets:** Create a `.streamlit/secrets.toml` file in your project directory with your API keys:
    ```toml
    GMAIL_API_KEY = "YOUR_GMAIL_API_KEY"
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
    ```
    * **GMAIL_API_KEY:** Obtain this key by setting up the Gmail API in the Google Cloud Console and creating credentials. Ensure you have enabled the Gmail API.
    * **GEMINI_API_KEY:** Get your API key from the Google AI Studio ([https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)).

2.  **Gmail API Credentials:** Download your Gmail API credentials JSON file (e.g., `credentials.json`) from the Google Cloud Console. Place this file in the root of your project directory.

3.  **Google API Key for Gemini:** As mentioned above, the Gemini API key should be stored in your Streamlit secrets.

## Usage Instructions

1.  **Run the Streamlit application:**
    ```bash
    streamlit run agent1_generate_problem.py
    ```

2.  **Follow the on-screen instructions:** The application will guide you through the initial setup, including:
    * Authenticating with your Gmail account.
    * Providing your LeetCode username (optional, but recommended for personalized tracking).
    * Setting your preferred difficulty level.

3.  **Receive daily problems:** Once configured, you will receive a new coding problem in your Gmail inbox each day.

4.  **Interact with the application:** Use the Streamlit interface to:
    * View your problem-solving history.
    * Review past problems using the spaced repetition feature.
    * Adjust your preferences.

## Example Workflow

1.  **First-time setup:** Run the application and follow the prompts to authenticate Gmail, provide your LeetCode username, and set your initial difficulty.
2.  **Daily practice:** Each morning, you'll find a new coding problem in your inbox. Solve it on LeetCode.
3.  **Problem tracking:** The application automatically (or manually, depending on implementation) updates your solved problem history.
4.  **Intelligent recommendations:** Based on your performance and history, Gemini AI selects the next problem, adjusting the difficulty as needed.
5.  **Spaced repetition:** The application reminds you to revisit previously solved problems at increasing intervals to solidify your understanding.
6.  **Progress monitoring:** Use the Streamlit interface to track your progress and identify areas where you might need more practice.

## File Descriptions

* `agent1_generate_problem.py`: This is the main Python script that runs the Streamlit application, handles problem generation, Gmail integration, and AI interactions.
* `leetcode_question.csv`: This file serves as a database of LeetCode problems, potentially containing information like problem title, difficulty, and links.
* `requirements.txt`: This file lists all the necessary Python packages and their versions required to run the application.
* `.streamlit/secrets.toml`: This file securely stores your API keys for Gmail and Gemini. **Ensure this file is not committed to version control.**
* `credentials.json`: This file contains your Gmail API service account credentials. **Ensure this file is kept secure and not publicly shared.**

## Dependencies

The application relies on the following Python libraries:

* `streamlit`: For creating the interactive web interface.
* `pandas`: For data manipulation, especially for handling the `leetcode_question.csv` file.
* `google-generativeai`: For interacting with Google's Gemini AI models.
* `google-api-python-client`: For interacting with the Gmail API.
* `google-auth-httplib2`: For authenticating with Google APIs.
* `google-auth-oauthlib`: For handling the OAuth 2.0 flow for Gmail.

## Setup Requirements

Before running Coding Coach, ensure you have the following:

* **Python 3.6 or higher** installed on your system.
* **A Google Cloud Project** with the Gmail API enabled.
* **Gmail API credentials** configured for your project.
* **A Google AI Studio account** to obtain a Gemini API key.
* **Streamlit installed** in your Python environment.

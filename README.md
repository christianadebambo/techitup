# TechItUp: AI-Powered Coding Learning Chatbot

TechItUp is an interactive web application designed to assist coding enthusiasts in learning and practicing programming concepts. Powered by OpenAI's GPT-3, it provides instant responses to coding questions, tutorials, and challenges.

## Features

1. **AI-Powered Chatbot**: Ask any programming-related questions and get instant answers.
2. **Tutorials**: Get tutorials on specific coding topics across various languages.
3. **Coding Challenges**: Receive coding challenges to solve and get instant feedback on your solutions.
4. **Progress Tracking**: View your past questions, challenges, and the feedback received.
5. **User Registration and Login**: Create an account and track your progress over time.

## Dependencies

- `streamlit`: For creating the web app interface.
- `openai`: To interact with the OpenAI GPT-3 API.
- `sqlite3`: For database operations.
- `bcrypt`: For hashing and verifying passwords.

## Setup

1. **Clone the Repository**: 
   
   ```
   git clone <repository_url>
   ```

2. **Install Dependencies**:

   Navigate to the project directory and install the necessary libraries:

   ```
   pip install -r requirements.txt
   ```

3. **Set Up OpenAI API Key**:

   You'll need an API key from OpenAI. Once you have the key, add it to the `secrets.toml` file in Streamlit sharing or to a `.streamlit/secrets.toml` file for local development. The file should look like:

   ```toml
   [openai]
   api_key = "YOUR_API_KEY_HERE"
   ```

4. **Run the App**:

   In the project directory, run:

   ```
   streamlit run app.py
   ```

## Usage

1. **Login/Register**: Start by creating an account or logging in if you already have one.
2. **Initial Assessment**: New users will be prompted to take an initial assessment to gauge their current coding knowledge.
3. **Chat with the Bot**: Ask any coding-related questions.
4. **Tutorials**: Choose a programming language and topic to receive a tutorial.
5. **Challenges**: Get a coding challenge, submit your solution, and receive feedback.

## Feedback

If you have any feedback or suggestions, please open an issue in this repository.

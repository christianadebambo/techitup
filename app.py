import streamlit as st
import openai
import sqlite3
import bcrypt

# Initialize OpenAI API
try:
    openai.api_key = st.secrets["openai"]["api_key"]
except KeyError:
    st.error("API Key not found in secrets.")
    st.stop()

# Database setup
try:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # User table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, 
            password TEXT, 
            interest TEXT, 
            goal TEXT,
            assessment_score INTEGER
        )
    ''')

    # User questions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_questions (
            id INTEGER PRIMARY KEY,
            username TEXT, 
            question TEXT, 
            answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User challenges table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_challenges (
            id INTEGER PRIMARY KEY,
            username TEXT, 
            challenge TEXT, 
            solution TEXT,
            feedback TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Feedback table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY,
            username TEXT, 
            question TEXT, 
            answer TEXT,
            feedback TEXT,
            helpful INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
except sqlite3.Error as e:
    st.error("Database error: " + str(e))
    st.stop()

# At the beginning of the script, initialize the session state for username if it doesn't exist yet
if 'username' not in st.session_state:
    st.session_state.username = None
    st.session_state.show_feedback = False  # New state variable

if 'tutorial_content' not in st.session_state:
    st.session_state.tutorial_content = None
if 'challenge_content' not in st.session_state:
    st.session_state.challenge_content = None

def get_gpt_response(prompt, language=None, score=None):
    try:
        # Add context based on the language and score
        context = ""
        if language:
            context += f"As a reminder, the user's primary coding language is {language}. "
        if score is not None:
            if score > 2:
                context += f"The user has a good understanding of basic programming concepts. "
            else:
                context += f"The user needs more guidance on basic programming concepts. "
        
        # Combine context and prompt
        full_prompt = context + prompt

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant. Provide a concise answer with code snippets (where necessary)."},
                {"role": "user", "content": full_prompt}
            ],
        )
        return response['choices'][0]['message']['content']
    except openai.error.OpenAIError as e:
        st.error("There was an issue with the AI service. Please try again later.")
        st.stop()

def get_gpt_tutorial(topic, level, language):
    prompt = f"Provide a {level} tutorial on {topic} for {language}."
    response = get_gpt_response(prompt)
    return response

def get_gpt_challenge(topic, level, language):
    prompt = f"Generate a {level} coding challenge related to {topic} for {language}."
    response = get_gpt_response(prompt)
    return response

def tutorials_page():
    st.title("Tutorials")
    language = st.text_input("Choose a programming language (e.g Python, JavaScript, Java)")
    topic = st.text_input("Enter a topic (e.g. 'lists', 'functions')")
    level = st.selectbox("Select difficulty level", ["beginner", "intermediate", "advanced"])
    
    if st.button("Get Tutorial"):
        # Remove previous tutorial content from session state
        st.session_state.tutorial_content = None
        with st.spinner('Generating tutorial...'):
            st.session_state.tutorial_content = get_gpt_tutorial(topic, level, language)
        st.write(st.session_state.tutorial_content)

def challenges_page():
    st.title("Coding Challenges")
    language = st.text_input("Choose a programming language (e.g Python, JavaScript, Java)")
    topic = st.text_input("Enter a topic for the challenge (e.g. 'lists', 'OOP')")
    level = st.selectbox("Select difficulty level", ["beginner", "intermediate", "advanced"])
    
    if st.button("Get Challenge"):
        with st.spinner('Generating challenge...'):
            st.session_state.challenge_content = get_gpt_challenge(topic, level, language)
        st.write(f"Challenge: {st.session_state.challenge_content}")

        # Once the challenge is generated, show the user input for solutions
        display_solution_input()
    elif 'challenge_content' in st.session_state and st.session_state.challenge_content:
        st.write(f"Challenge: {st.session_state.challenge_content}")

        # If the challenge already exists in the session state, show the user input for solutions
        display_solution_input()

def display_solution_input():
    user_solution = st.text_area("Write your solution here...")
    if st.button("Submit Solution"):
        if 'submit_solution' not in st.session_state:
            st.session_state.submit_solution = False
        if not st.session_state.submit_solution:
            st.session_state.submit_solution = True
            with st.spinner('Getting feedback...'):
                # Ask GPT-3.5 Turbo for feedback on the submitted solution.
                feedback_prompt = f"Provide feedback on this solution for this challenge: '{user_solution}'"
                feedback = get_gpt_response(feedback_prompt)
                st.write(f"Feedback: {feedback}")
                # Store the user challenge and feedback
                store_user_challenge(st.session_state.username, st.session_state.challenge_content, user_solution, feedback)
        else:
            st.session_state.submit_solution = False

def register_user(username, password, interest, goal):
    try:
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, interest, goal) VALUES (?, ?, ?, ?)", 
                      (username, hashed_pw, interest, goal))
            conn.commit()
    except sqlite3.Error as e:
        st.error("There was an issue with the database operation. Please try again later.")

def check_user(username, password):
    try:
        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username=?", (username,))
            stored_pw = c.fetchone()
            if stored_pw and bcrypt.checkpw(password.encode('utf-8'), stored_pw[0]):
                return True
        return False
    except sqlite3.Error as e:
        st.error("There was an issue with the database operation. Please try again later.")
        return False

def store_assessment_result(username, score):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET assessment_score = ? WHERE username = ?", (score, username))
        conn.commit()

def user_exists(username):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username=?", (username,))
        return bool(c.fetchone())

def has_taken_assessment(username):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT assessment_score FROM users WHERE username=?", (username,))
        score = c.fetchone()[0]
        return score is not None

def registration_page():
    st.title("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    interest = st.selectbox("Your primary coding language", ["C#", "VBA", "Python", "Java", "SQL"])
    goal = st.text_area("What are your coding goals?")
    if st.button("Register"):
        if user_exists(username):
            st.error("User already exists!")
        elif password == confirm_password:
            register_user(username, password, interest, goal)
            st.session_state.username = username  # Update session state
            st.session_state.next_page = "Assessment"  # Indicate that the next page is Assessment
            st.experimental_rerun()  # Rerun to navigate
        else:
            st.error("Passwords do not match!")

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_user(username, password):
            st.success("Logged in successfully!")
            st.session_state.username = username  # Update the session state
            if not has_taken_assessment(username):
                st.session_state.next_page = "Assessment"
            else:
                st.session_state.next_page = "Chat"
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    return "Login"  # By default, stay on the Login page

csharp_questions = {
    "What does the keyword 'public' mean in C#?": ["Accessible only within the same class", "Accessible throughout the same namespace", "Accessible from any assembly", "Accessible only within the same file"],
    "What is the purpose of the 'using' statement in C#?": ["Declaring variables", "Defining a class", "Managing resources like file handling", "Loop control"],
    "Which of the following data types is not available in C#?": ["int", "char", "double", "variant"],
    "What does 'LINQ' stand for in C#?": ["Language-Integrated Query", "Linked Information Network Query", "Looping Integrated Query", "Logical Interaction Query"],
    "What is a 'delegate' in C# used for?": ["Managing file I/O", "Error handling", "Representing a reference to a method", "Defining database schemas"]
}

csharp_answers = {
    "What does the keyword 'public' mean in C#?": "Accessible from any assembly",
    "What is the purpose of the 'using' statement in C#?": "Managing resources like file handling",
    "Which of the following data types is not available in C#?": "variant",
    "What does 'LINQ' stand for in C#?": "Language-Integrated Query",
    "What is a 'delegate' in C# used for?": "Representing a reference to a method"
}

vba_questions = {
    "What does VBA stand for?": ["Visual Basic for Applications", "Very Basic Application", "Virtual Business Automation", "Vital Business Analysis"],
    "In VBA, which object is used to interact with Excel worksheets?": ["Forms", "Workbooks", "Folders", "Frames"],
    "What is a 'macro' in VBA?": ["A type of variable", "A spreadsheet cell", "A recorded sequence of actions", "A loop construct"],
    "Which VBA function is used to display a message box?": ["msgBox()", "popUpBox()", "displayMsg()", "showMessage()"],
    "What file extension is commonly associated with VBA macro-enabled Excel files?": [".xls", ".csv", ".vba", ".xlsm"]
}

vba_answers = {
    "What does VBA stand for?": "Visual Basic for Applications",
    "In VBA, which object is used to interact with Excel worksheets?": "Workbooks",
    "What is a 'macro' in VBA?": "A recorded sequence of actions",
    "Which VBA function is used to display a message box?": "msgBox()",
    "What file extension is commonly associated with VBA macro-enabled Excel files?": ".xlsm"
}

python_questions = {
    "Which of the following is used to define a comment in Python?": ["// Comment", "/* Comment */", "# Comment", "-- Comment"],
    "How do you import an external Python module?": ["import module_name", "include module_name", "add module_name", "require module_name"],
    "What does the len() function do in Python?": ["Convert to lowercase", "Calculate the length of a string or list", "Remove elements from a list", "Format text"],
    "Which Python data structure stores an ordered, changeable collection with no duplicate elements?": ["Array", "Dictionary", "Set", "Tuple"],
    "How do you open and read a text file in Python?": ["open_file()", "read_file()", "with open() as file:", "file.open() and file.read()"]
}

python_answers = {
    "Which of the following is used to define a comment in Python?": "# Comment",
    "How do you import an external Python module?": "import module_name",
    "What does the len() function do in Python?": "Calculate the length of a string or list",
    "Which Python data structure stores an ordered, changeable collection with no duplicate elements?": "Set",
    "How do you open and read a text file in Python?": "with open() as file:"
}

java_questions = {
    "What is the entry point for a Java application?": ["main()", "start()", "run()", "execute()"],
    "Which access modifier is used for a variable that should only be accessible within its own class in Java?": ["public", "private", "protected", "static"],
    "In Java, what is a 'NullPointerException'?": ["An exception thrown when dividing by zero", "An exception caused by a missing import statement", "An exception indicating that an object is not initialized", "An exception when a loop runs infinitely"],
    "What is a 'constructor' in Java used for?": ["Initializing a class's fields", "Performing mathematical calculations", "Creating loops", "Running database queries"],
    "Which Java keyword is used to implement inheritance between classes?": ["inherit", "extend", "implement", "interface"]
}

java_answers = {
    "What is the entry point for a Java application?": "main()",
    "Which access modifier is used for a variable that should only be accessible within its own class in Java?": "private",
    "In Java, what is a 'NullPointerException'?": "An exception indicating that an object is not initialized",
    "What is a 'constructor' in Java used for?": "Initializing a class's fields",
    "Which Java keyword is used to implement inheritance between classes?": "extend"
}

sql_questions = {
    "What does SQL stand for?": ["Structured Query Language", "Simple Query Language", "Standard Query Logic", "Structured Query Logic"],
    "Which SQL statement is used to retrieve data from a database?": ["SELECT", "RETRIEVE", "GET", "QUERY"],
    "What is an SQL 'JOIN' clause used for?": ["Splitting a table into two tables", "Combining rows from two or more tables", "Deleting data from a table", "Sorting data"],
    "What SQL clause is used to filter the results of a query?": ["SORT BY", "FILTER", "GROUP BY", "WHERE"],
    "In SQL, which type of key uniquely identifies each row in a table?": ["Primary Key", "Foreign Key", "Super Key", "Composite Key"]
}

sql_answers = {
    "What does SQL stand for?": "Structured Query Language",
    "Which SQL statement is used to retrieve data from a database?": "SELECT",
    "What is an SQL 'JOIN' clause used for?": "Combining rows from two or more tables",
    "What SQL clause is used to filter the results of a query?": "WHERE",
    "In SQL, which type of key uniquely identifies each row in a table?": "Primary Key"
}

# Define questions and answers for each language
question_bank = {
    "C#": {
        "questions": csharp_questions,
        "answers": csharp_answers
    },
    "VBA": {
        "questions": vba_questions,
        "answers": vba_answers
    },
    "Python": {
        "questions": python_questions,
        "answers": python_answers
    },
    "Java": {
        "questions": java_questions,
        "answers": java_answers
    },
    "SQL": {
        "questions": sql_questions,
        "answers": sql_answers
    }
}

def assessment_page(username):
    st.title("Initial Assessment")
    
    # Fetch user's primary interest
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT interest FROM users WHERE username=?", (username,))
        interest = c.fetchone()[0]

    # Get questions and answers based on interest
    questions = question_bank[interest]["questions"]
    correct_answers = question_bank[interest]["answers"]

    user_answers = {}
    with st.form(key='assessment_form'):
        for question, options in questions.items():
            user_answers[question] = st.radio(question, options)
        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        correct_count = sum([1 for question, answer in user_answers.items() if answer == correct_answers[question]])
        store_assessment_result(username, correct_count)  # Store the user's score
        st.session_state.next_page = "Feedback"  # Indicate that the next page is Feedback
        st.experimental_rerun()

def chatbot_interface(username=None):
    st.title("TechItUp AI-Powered Coding Learning Chatbot")
    st.write("Welcome to the TechItUp AI-powered coding learning chatbot!")
    st.write("This chatbot will assist you in learning coding concepts. Ask any programming-related questions, and let's get started!")
    st.markdown("[Click here for a coding challenge](https://edabit.com/challenges)")
    st.markdown("[Start a quiz](https://www.codeconquest.com/coding-quizzes/)")
    
    # Check if conversation exists in session state, otherwise initialize it as an empty list
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []

    # Display the conversation history
    for item in st.session_state.conversation:
        if item['role'] == 'user':
            st.write(f"You: {item['content']}")
        else:
            st.write(f"Chatbot: {item['content']}")
    
    # Input field for the user's question
    new_input = st.text_input("Type your question here...")

    # Fetch user's primary interest and assessment score
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT interest, assessment_score FROM users WHERE username=?", (username,))
        interest, score = c.fetchone()

    if new_input and new_input not in [item['content'] for item in st.session_state.conversation]:
        st.session_state.conversation.append({'role': 'user', 'content': new_input})
        with st.spinner('Processing...'):
            chatbot_response = get_gpt_response(new_input, interest, score)
            
        # Store the user question and the chatbot's answer
        store_user_question(username, new_input, chatbot_response)
        
        st.session_state.conversation.append({'role': 'chatbot', 'content': chatbot_response})

        # Display the chatbot's immediate response
        st.write(f"Chatbot: {chatbot_response}")

         # Feedback collection mechanism
        if 'feedback_collected' not in st.session_state:
            st.session_state.feedback_collected = False

        if not st.session_state.feedback_collected:
            helpful = st.button("Yes, it was helpful")
            not_helpful = st.button("No, it wasn't helpful")

            if helpful:
                store_user_feedback(username, new_input, chatbot_response, None, 1)  # 1 indicates the answer was helpful
                st.session_state.feedback_collected = True

            if not_helpful:
                store_user_feedback(username, new_input, chatbot_response, None, 0)  # 0 indicates the answer was not helpful
                st.session_state.feedback_collected = True


def store_user_feedback(username, question, answer, feedback, helpful):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO user_feedback (username, question, answer, feedback, helpful) VALUES (?, ?, ?, ?, ?)", 
                  (username, question, answer, feedback, helpful))
        conn.commit()

def feedback_page(username):
    st.title("Assessment Feedback")
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT assessment_score FROM users WHERE username=?", (username,))
        score = c.fetchone()[0]
    st.success(f"You answered {score} out of 5 questions correctly!")
    if score > 2:
        st.write("Great job! You have a good understanding of basic programming concepts.")
    else:
        st.write("Keep practicing! You'll get better with time.")
    if st.button("Proceed to Chat"):
        st.session_state.next_page = "Chat"
        st.experimental_rerun()

def store_user_question(username, question, answer):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO user_questions (username, question, answer) VALUES (?, ?, ?)", 
                  (username, question, answer))
        conn.commit()

def store_user_challenge(username, challenge, solution, feedback):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO user_challenges (username, challenge, solution, feedback) VALUES (?, ?, ?, ?)", 
                  (username, challenge, solution, feedback))
        conn.commit()

def progress_page(username):
    st.title("Your Progress")
    
    # Fetch user questions and answers
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT question, answer, timestamp FROM user_questions WHERE username = ? ORDER BY timestamp DESC", (username,))
        questions = c.fetchall()

        c.execute("SELECT challenge, solution, feedback, timestamp FROM user_challenges WHERE username = ? ORDER BY timestamp DESC", (username,))
        challenges = c.fetchall()

    st.write("### Questions & Answers")
    for q, a, t in questions:
        st.write(f"**{t}**")
        st.write(f"**Q:** {q}")
        st.write(f"**A:** {a}")
        st.write("---")

    st.write("### Challenges & Feedback")
    for ch, sol, f, t in challenges:
        st.write(f"**{t}**")
        st.write(f"**Challenge:** {ch}")
        st.write(f"**Your Solution:** {sol}")
        st.write(f"**Feedback:** {f}")
        st.write("---")

def logout():
    st.session_state.username = None  # Reset the username in session state
    st.experimental_rerun()  # Rerun the app to show the login/register page

if __name__ == "__main__":
    try:
        if not st.session_state.username:
            action = st.radio("Choose an action", ["Login", "Register"])
            if action == "Login":
                next_page = login_page()
                if next_page != "Login":
                    st.experimental_rerun()
            elif action == "Register":
                registration_page()
        else:
            # Check if the user has taken the assessment
            user_has_taken_assessment = has_taken_assessment(st.session_state.username) if st.session_state.username else False

            # If the user is logged in and has taken the assessment, show the sidebar
            if st.session_state.username and user_has_taken_assessment:
                sidebar_option = st.sidebar.selectbox("Choose an option", ["Chat", "Tutorials", "Challenges", "Progress", "Logout"])
            else:
                sidebar_option = "Chat"  # Default option for users not logged in or those who haven't taken the assessment
                
            if sidebar_option == "Chat":
                if 'next_page' not in st.session_state or st.session_state.next_page == "Assessment":
                    assessment_page(st.session_state.username)
                elif st.session_state.next_page == "Feedback":
                    feedback_page(st.session_state.username)
                else:
                    chatbot_interface(st.session_state.username)
            elif sidebar_option == "Tutorials":
                tutorials_page()
            elif sidebar_option == "Challenges":
                challenges_page()
            elif sidebar_option == "Progress":
                progress_page(st.session_state.username)
            elif sidebar_option == "Logout":
                logout()
    except Exception as e:
        st.error("An unexpected error occurred: " + str(e))

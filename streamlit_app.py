# import the packages required
import streamlit as st
from openai import OpenAI
from utils import (
    delete_files,
    delete_thread,
    EventHandler,
    moderation_endpoint,
    is_nsfw,
    # is_not_question,
    render_custom_css,
    render_download_files,
    retrieve_messages_from_thread,
    retrieve_assistant_created_files
)
import pandas as pd

# Import additional libraries for Lottie animations
from streamlit_lottie import st_lottie
import requests

# setting up the page configuration
st.set_page_config(
    page_title="RMB E-Trading",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Function to load Lottie animations
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


# custom css for styling
def inject_custom_css():
    st.markdown(
        """
        <style>
            /* Custom CSS styles */
            body {
                background-color: #0e1117;
                color: #c9d1d9;
            }
            /* Increase the size of login input boxes */
            .stTextInput > div > div > input {
                height: 50px;
                font-size: 20px;
            }
            /* Additional styles */
        </style>
    """,
        unsafe_allow_html=True,
    )


# inject the custom css
inject_custom_css()

# initialize session state variables for login to keep track of the user's login status and username.
if "login_status" not in st.session_state:
    st.session_state["login_status"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None


# function for the login page
def login():
    # Load the Lottie animation
    lottie_animation = load_lottieurl("https://lottie.host/06d4c26a-6c88-4a0d-9f13-b12cb95d5d8f/SPKKrz3jZI.json")

    # Display the animation above the login form
    st_lottie(lottie_animation, height=300)

    st.subheader("🔐 Login to RMB E-Trading Platform")
    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")
    login_col1, login_col2, login_col3 = st.columns([2, 1, 2])
    with login_col2:
        login_button = st.button("Login")

    # Set username and password check
    if login_button:
        if username == "etrading" and password == "hello new world":  # Updated credentials
            st.session_state["login_status"] = True
            st.session_state["username"] = username
            st.success("Login successful!")
        else:
            st.error("Invalid username or password.")


# Check login status and proceed accordingly
if not st.session_state["login_status"]:
    login()
else:
    # Sidebar Navigation
    # Load the Lottie animation
    lottie_animation_sidebar = load_lottieurl(
        "https://lottie.host/7c9e8fa9-bfcf-4716-808d-a98756a25b53/8JuwlhCVLC.json")

    # Display the animation in the sidebar
    with st.sidebar:
        st_lottie(lottie_animation_sidebar, height=200)
        st.markdown("## Navigation")
        # set choice for the different tabs
        nav_choice = st.radio("", ["Analyze Data", "Download Results"])

    # Initialize OpenAI Client and Assistant After Successful Login
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    # Retrieve the assistant
    assistant = client.beta.assistants.retrieve(st.secrets["ASSISTANT_ID"])

    # Initialize session state variables
    if "file_id" not in st.session_state:
        st.session_state["file_id"] = [st.secrets["FILE_ID"]]
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = None
    if "text_boxes" not in st.session_state:
        st.session_state["text_boxes"] = []
    if "assistant_text" not in st.session_state:
        st.session_state["assistant_text"] = [""]
    if "code_input" not in st.session_state:
        st.session_state["code_input"] = []
    if "code_output" not in st.session_state:
        st.session_state["code_output"] = []
    if "analysis_complete" not in st.session_state:
        st.session_state["analysis_complete"] = False
    if "clear_input" not in st.session_state:
        st.session_state["clear_input"] = False

    # THE ANALYZE DATA TAB
    # --------------------
    if nav_choice == "Analyze Data":
        st.subheader("📁 Welcome to the E-Trading Data Analysis Tool")
        st.markdown(
            "This is a proof of concept using synthetic data. The reason behind this approach is to get something out as quickly as possible while ensuring the security of the data."
        )
        # display a snapshot of the data from the assets folder
        try:
            df = pd.read_csv('assets/etrading_synthetic_data.csv')
            st.write("Here's a snapshot of your data:")
            st.dataframe(df.head(10))
        except Exception as e:
            st.error(f"Failed to load data: {e}")
        st.markdown(
            "Ask questions about your data. You can keep asking follow-up questions until you're satisfied."
        )

        # Add pre-written questions
        st.markdown("### Or choose from some pre-written questions:")
        pre_written_questions = [
            "What is the average trade volume?",
            "flag interesting trades and return a neat table",
            "look at trades done per friendly name and return a stacked bar with the lion king colors for currency traded",
            "find which clients are ahead of market trends and which clients are lagging and return names in a table",
            "Are there any outliers in the data?"
        ]

        # Display pre-written questions as buttons
        for idx, q in enumerate(pre_written_questions):
            if st.button(q, key=f"pre_written_{idx}"):
                def submit_question(question):
                    # Send the question to the assistant
                    client.beta.threads.messages.create(
                        thread_id=st.session_state["thread_id"],
                        role="user",
                        content=question,
                    )

                    # Display the user's question
                    st.session_state.text_boxes.append(st.empty())
                    st.session_state.text_boxes[-1].success(f"**> 🤔 User:** {question}")

                    # Create the optica around returning the response
                    with st.spinner("Analyzing your question. Please wait..."):
                        with client.beta.threads.runs.stream(
                                thread_id=st.session_state["thread_id"],
                                assistant_id=assistant.id,
                                event_handler=EventHandler(),
                                temperature=0,
                        ) as stream:
                            stream.until_done()

                    st.success("✅ Analysis complete!")


                submit_question(q)

        # Start a new thread if not already started
        if not st.session_state["thread_id"]:
            thread = client.beta.threads.create()
            st.session_state["thread_id"] = thread.id

            # Update the thread's tool_resources to include the uploaded files
            client.beta.threads.update(
                thread_id=st.session_state["thread_id"],
                tool_resources={"code_interpreter": {"file_ids": st.session_state['file_id']}}
            )

        # Display conversation history using text boxes
        assistant_messages = retrieve_messages_from_thread(st.session_state['thread_id'])
        st.session_state.assistant_created_file_ids = retrieve_assistant_created_files(assistant_messages)
        st.session_state.download_files, st.session_state.download_file_names = render_download_files(
            st.session_state.assistant_created_file_ids)
        for idx, (file, name) in enumerate(
                zip(st.session_state.download_files, st.session_state.download_file_names)):
            st.download_button(f"Download {name}", file, key=idx)

        # Allow the user to input a question after the conversation history
        # Check if we need to clear the input field
        if st.session_state.get("clear_input", False):
            st.session_state["input_question"] = ""
            st.session_state["clear_input"] = False

        # Buttons to press for analyzing the data
        st.divider()
        question = st.text_input("💬 Ask a question about the data:", key="input_question")
        analyze_col1, analyze_col2 = st.columns([1, 1])
        with analyze_col1:
            analyze_btn = st.button("Submit Question", key="submit_question")
        with analyze_col2:
            finish_btn = st.button("Finish Analysis", key="finish_analysis")

        if analyze_btn and question:
            def submit_question(question):
                # Send the question to the assistant
                client.beta.threads.messages.create(
                    thread_id=st.session_state["thread_id"],
                    role="user",
                    content=question,
                )

                # Display the user's question
                st.session_state.text_boxes.append(st.empty())
                st.session_state.text_boxes[-1].success(f"**> 🤔 User:** {question}")

                # Create the optica around returning the response
                with st.spinner("Analyzing your question. Please wait..."):
                    with client.beta.threads.runs.stream(
                            thread_id=st.session_state["thread_id"],
                            assistant_id=assistant.id,
                            tool_choice={"type": "code_interpreter"},
                            event_handler=EventHandler(),
                            temperature=0
                    ) as stream:
                        stream.until_done()

                st.success("✅ Analysis complete!")


            submit_question(question)

        if finish_btn:
            st.session_state["analysis_complete"] = True
            st.success("You have finished the analysis.")

    elif nav_choice == "Download Results" and st.session_state["analysis_complete"]:
        st.subheader("📥 Download Results")
        st.markdown("Download the results of your data analysis.")

        with st.spinner("Preparing files for download..."):
            assistant_messages = retrieve_messages_from_thread(st.session_state["thread_id"])
            st.session_state.assistant_created_file_ids = retrieve_assistant_created_files(
                assistant_messages
            )
            (
                st.session_state.download_files,
                st.session_state.download_file_names,
            ) = render_download_files(st.session_state.assistant_created_file_ids)
            for idx, (file, name) in enumerate(
                    zip(st.session_state.download_files, st.session_state.download_file_names)
            ):
                st.download_button(f"💾 Download {name}", file, key=idx)

    else:
        if not st.session_state["file_id"]:
            st.subheader("📂 No Data Uploaded")
            st.markdown(
                "Please upload data in the **Upload Data** section to start analysis."
            )
        elif not st.session_state["analysis_complete"]:
            st.subheader("🔎 Analysis Incomplete")
            st.markdown(
                "Please complete your analysis in the **Analyze Data** section."
            )
        else:
            st.subheader("📥 No Results Available")
            st.markdown("No results are available for download.")


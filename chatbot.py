import streamlit as st
from streamlit_chat import message
import requests
import wikipediaapi
import pdfplumber  
import spacy
import re
import io

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Wikipedia API setup
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent="AgenticChatbot/1.0 (techbeast1004@gmail.com)",
    language='en'
)

# SERPAPI constants
SERPAPI_API_KEY = "e86e8dea688c561e0c31ee93eeb78d0a985f31b7789e21be8b3580cb4a7c6779"
SEARCH_ENGINE = "google"

# Function for web search using SERPAPI
def web_search(query):
    url = f"https://serpapi.com/search.json"
    params = {
        "engine": SEARCH_ENGINE,
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": 3
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("organic_results", [])
        if not results:
            return "No results found."
        
        search_results = ""
        for idx, result in enumerate(results, 1):
            title = result.get("title", "No title")
            link = result.get("link", "No link")
            search_results += f"{idx}. {title}: {link}\n\n"

        return search_results

    except requests.RequestException as e:
        return f"An error occurred during the search: {e}"

# Wikipedia search function using Wikipedia-API
def wikipedia_search(query):
    formatted_query = query.title().strip()
    page = wiki_wiki.page(formatted_query)
    
    if not page.exists():
        return "Sorry, I couldn't find any information on that topic on Wikipedia."
    
    summary = f"{page.summary[0:2000]}..." 
    return summary

# Process uploaded files (PDF and Text)
def process_uploaded_file(uploaded_file):
    file_type = uploaded_file.type
    if file_type == "application/pdf":
        return extract_text_from_pdf(uploaded_file)
    elif file_type == "text/plain":
        return extract_text_from_text_file(uploaded_file)
    else:
        return "Unsupported file format. Please upload a PDF or a text file."

def extract_text_from_pdf(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text.strip()
    except Exception as e:
        return f"Error extracting text from PDF: {e}"

def extract_text_from_text_file(txt_file):
    try:
        text = txt_file.read().decode("utf-8")
        return text.strip()
    except Exception as e:
        return f"Error extracting text from file: {e}"

# Function to extract resume data using SpaCy
def extract_resume_data(text):
    doc = nlp(text)
    
    resume_data = {
        "Name": None,
        "Email": None,
        "Phone": None,
        "Skills": [],
        "Work Experience": [],
        "Education": [],
        "Projects": [],
    }

    # Regex patterns
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"\+?[0-9]{1,3}?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}"
    marks_pattern = r"\b([0-9]{1,2}(\.[0-9]{1,2})?%)?\b"

    # Extract name (Assuming the first entity is the name)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            resume_data["Name"] = ent.text
            break  # Assume the first PERSON entity is the name
    
    # Extract email
    emails = re.findall(email_pattern, text)
    if emails:
        resume_data["Email"] = emails[0]
    
    # Extract phone
    phones = re.findall(phone_pattern, text)
    if phones:
        resume_data["Phone"] = phones[0]
    
    # Extract skills based on common patterns (e.g., "Python", "Java", "C++")
    skills_keywords = ["python", "java", "c++", "javascript", "html", "css", "sql", "machine learning", "deep learning", "data analysis"]
    resume_data["Skills"] = [skill for skill in skills_keywords if skill.lower() in text.lower()]
    
    # Extract Work Experience and Education sections based on keywords
    experience_keywords = ["work experience", "experience", "job", "internship"]
    education_keywords = ["education", "degree", "university", "college"]
    
    resume_data["Work Experience"] = [sent.text for sent in doc.sents if any(keyword in sent.text.lower() for keyword in experience_keywords)]
    resume_data["Education"] = [sent.text for sent in doc.sents if any(keyword in sent.text.lower() for keyword in education_keywords)]
    
    # Extract Projects
    project_keywords = ["project", "worked on", "developed", "built", "created"]
    resume_data["Projects"] = [sent.text for sent in doc.sents if any(keyword in sent.text.lower() for keyword in project_keywords)]
    
    # Extract Marks (Percentage or GPA)
    marks = re.findall(marks_pattern, text)
    resume_data["Marks"] = marks
    
    return resume_data

# Dynamic response based on resume data (education, work, and skills)
def generate_dynamic_response(resume_data):
    response = ""
    
    # Provide advice based on education
    if resume_data["Education"]:
        response += "Based on your education background, you have completed:\n"
        for edu in resume_data["Education"]:
            response += f"- {edu}\n"
        
        # Suggest future education options
        response += "\nIf you're interested in further education, you could consider the following paths:\n"
        if "computer science" in str(resume_data["Education"]).lower() or "engineering" in str(resume_data["Education"]).lower():
            response += "- Pursuing a Master's degree in Data Science, Machine Learning, or Artificial Intelligence.\n"
            response += "- Obtaining professional certifications in cloud computing (e.g., AWS, Azure) or cybersecurity.\n"
        else:
            response += "- Enrolling in technical courses or certifications to expand your knowledge in areas like web development, machine learning, or cloud infrastructure.\n"

    # Provide advice based on skills
    if resume_data["Skills"]:
        response += "\nYou have demonstrated skills in:\n"
        response += ", ".join(resume_data["Skills"]) + ".\n"
        
        # Recommend skill improvements
        response += "\nTo advance your career, consider developing expertise in:\n"
        if "python" in resume_data["Skills"]:
            response += "- Advanced Python topics like machine learning libraries (TensorFlow, PyTorch) and data processing with Pandas.\n"
        if "java" in resume_data["Skills"]:
            response += "- Building scalable back-end systems using Java frameworks such as Spring Boot.\n"
        if "javascript" in resume_data["Skills"]:
            response += "- Improving front-end skills by mastering frameworks like React or Angular.\n"
        if "sql" in resume_data["Skills"]:
            response += "- Learning more about database management, including NoSQL databases like MongoDB.\n"

    # Provide advice based on work experience
    if resume_data["Work Experience"]:
        response += "\nYour work experience includes:\n"
        for experience in resume_data["Work Experience"]:
            response += f"- {experience}\n"
        
        # Offer future job suggestions
        response += "\nTo move forward in your career, you might consider roles such as:\n"
        if "developer" in str(resume_data["Work Experience"]).lower():
            response += "- Software Developer, Full-Stack Engineer, or Data Scientist roles depending on your area of expertise.\n"
        else:
            response += "- Transitioning into technical roles or leadership positions in software development or data science.\n"

    # If no specific data is found, give general advice
    if not response:
        response = "It seems like I couldn't extract sufficient information from your resume to provide specific guidance. Could you provide more details about your education or work experience?"
    
    return response

# Detect intent of user input

# Detect intent of user input
def detect_intent(user_input):
    career_keywords = ["resume", "cv", "career", "job", "experience", "skills"]
    search_keywords = ["search", "google", "lookup"]
    wikipedia_keywords = ["wikipedia", "wiki", "information"]
    
    user_input = user_input.lower().strip()

    if any(keyword in user_input for keyword in wikipedia_keywords):
        return "wikipedia"
    elif any(keyword in user_input for keyword in career_keywords):
        return "career"
    elif any(keyword in user_input for keyword in search_keywords):
        return "search"
    else:
        return "general"

# Main chatbot function
def chatbot_response(user_input, uploaded_file=None):
    intent = detect_intent(user_input)
    
    if intent == "wikipedia":
        query = user_input.replace("wikipedia", "").replace("wiki", "").strip()
        if query:
            return wikipedia_search(query)
        else:
            return "Please specify a topic to search on Wikipedia."

    elif intent == "career" and uploaded_file is not None:
        text = process_uploaded_file(uploaded_file)
        resume_data = extract_resume_data(text)
        guidance = generate_dynamic_response(resume_data)
        return guidance
    
    elif intent == "search":
        return web_search(user_input)
    
    else:
        return f"You said: {user_input}"

# Streamlit UI setup
def on_btn_click():
    del st.session_state.past[:]
    del st.session_state.generated[:]
if 'past' not in st.session_state:
    st.session_state['past'] = []

if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'uploaded_file' not in st.session_state:
    st.session_state['uploaded_file'] = None  # Initialize uploaded_file

st.title("NerdBot - Your Personal Learning Assistant")

# File uploader for resume
uploaded_file = st.file_uploader("Upload your resume (PDF/Plain Text)", type=["pdf", "txt"])
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file

chat_placeholder = st.empty()

with chat_placeholder.container():
    for i in range(len(st.session_state['generated'])):
        message(st.session_state['past'][i], is_user=True, key=f"{i}_user")
        message(st.session_state['generated'][i], key=f"{i}")

def on_input_change():
    user_input = st.session_state.user_input
    response = chatbot_response(user_input, uploaded_file=st.session_state.uploaded_file)
    st.session_state.past.append(user_input)
    st.session_state.generated.append(response)

st.text_input("Ask me anything (e.g., 'wikipedia Bitcoin', 'search AI trends', 'analyze resume'or say 'give career advice')", key="user_input", on_change=on_input_change)
st.button("Clear chat", on_click=on_btn_click)
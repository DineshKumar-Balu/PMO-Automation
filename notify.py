# notify.py
import os
from twilio.rest import Client
from dotenv import load_dotenv
from dateutil import tz
import re
from datetime import datetime, timedelta

load_dotenv()
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

os.environ["GROQ_API_KEY"]= "GROQ_API_KEY"

llm1 = ChatGroq(
    model="llama3-70b-8192",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

system_prompt = (
    "You are a concise TODO list generator."
    " Given the following transcript, extract actionable tasks"
    " and present them as short, clear bullet points."
    " Provide a TODO list in this format: '- Task 1\n-Task2\n...'"
)

# Create the prompt template
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),  
        MessagesPlaceholder("chat_history"),  
        ("human", "{input}") 
    ]
)

def notifyuser(title, start_time, meet_link, ph_no):
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        body=f"Reminder: You are having a meeting titled: {title} at {start_time}. Click the link to join the meeting: {meet_link}",
        to=f"whatsapp:+91{ph_no}",
    )
    print(message.body)

def sendtodo(title,todo, ph_no):
    message = client.messages.create(
        from_="whatsapp:+14155238886",
        body= f"This is the todo list for {title}:\n {todo}",
        to=f"whatsapp:+91{ph_no}",
    )

def validate_phone_number(phone):
    """Validate phone number (must be a 10-digit number)."""
    pattern = r"^\d{10}$"
    return bool(re.match(pattern, phone))

def is_meeting_completed(end_time_dt):
    """Check if meeting end time has passed"""
    return datetime.now() > end_time_dt

def is_reminder_time(start_time_dt):
    """Check if current time is within 10 minutes of start time"""
    current_time = datetime.now(tz.tzlocal())  
    time_difference = start_time_dt - current_time
    return timedelta(minutes=0) <= time_difference <= timedelta(minutes=10)

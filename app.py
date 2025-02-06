import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime
import pickle
import re
import requests
import os
import time
import pandas as pd
from dateutil import tz
import webbrowser
from dateutil import parser
from notify import validate_phone_number, notifyuser, is_reminder_time, llm1, prompt_template,sendtodo

# Google API Scopes
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/drive.readonly'
]
# Set Streamlit page configuration
st.set_page_config(
    page_title="PMO Automation",
    page_icon="📅",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .header-row {
        background-color: #f8f9fa;
        padding: 12px 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: 600;
        color: #2c3e50;
    }
    .meeting-row {
        padding: 15px;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin: 8px 0;
        transition: box-shadow 0.2s;
    }
    .meeting-row:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .status-pill {
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
        display: inline-block;
    }
    .upcoming {
        background-color: #e3f2fd;
        color: #1976d2;
    }
    .in-progress {
        background-color: #fff3e0;
        color: #ef6c00;
    }
    .completed {
        background-color: #f5f5f5;
        color: #757575;
    }
    .stButton>button {
        padding: 6px 20px;
        border-radius: 20px;
    }

     /* Change expander hover color */
    .stExpander:hover {
        border-color: #1e90ff !important;
    }

    /* Change expander icon color */
    .stExpander .streamlit-expanderHeader svg {
        color: #1e90ff !important;
    }

    /* Change expander border color */
    .stExpander {
        border-color: #1e90ff;
    }
</style>
""", unsafe_allow_html=True)


def get_user_info(credentials):
    """Get user information from Google API"""
    try:
        people_service = build('people', 'v1', credentials=credentials)
        profile = people_service.people().get(
            resourceName='people/me',
            personFields='names,emailAddresses,phoneNumbers'
        ).execute()

        phone_number = None
        if 'phoneNumbers' in profile and profile['phoneNumbers']:
            phone_number = profile['phoneNumbers'][0].get('canonicalForm')
        return profile, phone_number
    except Exception as e:
        st.error(f"Error fetching user info: {str(e)}")
        return None, None


def get_google_credentials():
    """Handle Google OAuth authentication"""
    if 'credentials' not in st.session_state:
        st.session_state.update({
            'credentials': None,
            'user_info': None,
            'phone_number': None
        })

    if not st.session_state.credentials or st.session_state.credentials.expired:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri='http://localhost:8501'
        )

        if "code" in st.query_params:
            try:
                code = st.query_params["code"]
                st.query_params.clear()
                flow.fetch_token(code=code)
                st.session_state.credentials = flow.credentials
                st.session_state.user_info, st.session_state.phone_number = get_user_info(flow.credentials)
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
                st.stop()
        else:
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.markdown(f"""
                <div style='text-align: center; padding: 40px 20px;'>
                    <h1 style='margin-bottom: 30px;'>PMO Automation</h1>
                    <a href='{auth_url}' target="_self">
                        <button style='
                            background-color: #4285F4;
                            color: white;
                            padding: 12px 30px;
                            border: none;
                            border-radius: 25px;
                            font-size: 16px;
                            cursor: pointer;
                            transition: transform 0.2s;
                        '>
                            <img src="https://img.icons8.com/?size=100&id=V5cGWnc9R4xj&format=png&color=000000" 
                            style="width: 20px; height: 20px; margin-right: 8px;">
                            Sign in with Google
                        </button>
                    </a>
                    <p style='margin-top: 30px; color: #666;'>
                        Connect your Google account to view calendar meetings
                    </p>
                </div>
            """, unsafe_allow_html=True)
            st.stop()
    return st.session_state.credentials


def main():
    """Main application logic"""
    credentials = get_google_credentials()

    if credentials and st.session_state.user_info:
        # User Info Section
        user_name = st.session_state.user_info.get('names', [{}])[0].get('displayName', 'User')

        # Sidebar Configuration
        with st.sidebar:
            st.markdown(f"## 👨🏻‍💻 {user_name}")
            st.write(f"Welcome 👋 {user_name}")
            st.subheader(" ", divider="blue")
            # st.markdown("---")

            if st.session_state.phone_number:
                col1, col2 = st.columns([2, 3])
                col1.markdown(f"📱 **Phone:** {st.session_state.phone_number}")
                col2.markdown(
                    """
                    <a href="https://api.whatsapp.com/send/?phone=%2B14155238886&text=join+anything-event&type=phone_number&app_absent=0" 
                       target="_blank" 
                       style="text-decoration: none;">
                        <button style="background-color: rgb(0,204,0); 
                                    color: white; 
                                    border: none; 
                                    padding: 8px 15px; 
                                    font-size: 15px; 
                                    border-radius: 5px; 
                                    display: flex; 
                                    align-items: center;">
                            <img src="https://png.pngtree.com/png-clipart/20221019/original/pngtree-whatsapp-icon-png-image_8704827.png" 
                                 width="28" 
                                 height="18" 
                                 style="margin-right: 8px;"> 
                            WhatsApp
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.write("Verify your WhatsApp number to get reminders!")
                ph_no = st.text_input("Enter your phone number:")
                if validate_phone_number(ph_no):
                    st.session_state.phone_number = ph_no
                    st.rerun()

        # Main Content Area
        c1, c2, c3 = st.columns([2, 4, 2])
        c2.title("📅 PMO Automation")
        st.subheader("Your Upcoming Meetings", divider="blue")

        # Calendar Service
        calendar_service = build('calendar', 'v3', credentials=credentials)
        now = datetime.utcnow().isoformat() + 'Z'

        # Fetch Calendar Events
        events_result = calendar_service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            st.info("No upcoming meetings found in your calendar")
            return

        # Process Meetings Data
        meetings_data = []
        current_time = datetime.now().astimezone()  # Get current time with timezone

        for event in events:
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            end_time = event['end'].get('dateTime', event['end'].get('date'))

            try:
                # Parse datetimes
                start_dt = parser.parse(start_time)
                end_dt = parser.parse(end_time)

                # Convert to local timezone
                if start_dt.tzinfo is None:
                    # If datetime is naive, assume local timezone
                    start_dt = start_dt.replace(tzinfo=tz.tzlocal())
                else:
                    # If datetime is aware, convert to local timezone
                    start_dt = start_dt.astimezone(tz.tzlocal())

                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=tz.tzlocal())
                else:
                    end_dt = end_dt.astimezone(tz.tzlocal())

                # Format for display
                date_str = start_dt.strftime("%d %b %Y")
                time_range = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"

            except Exception as e:
                st.error(f"Error parsing event time: {str(e)}")
                date_str = time_range = "N/A"
                start_dt = end_dt = None

            # Status determination
            current_time = datetime.now(tz.tzlocal())
            status = "Upcoming"

            if start_dt and end_dt:
                if current_time > end_dt:
                    status = "Completed"
                elif start_dt <= current_time <= end_dt:
                    status = "In Progress"

            meetings_data.append({
                "title": event.get('summary', 'Untitled Meeting'),
                "date": date_str,
                "time": time_range,
                "link": event.get('hangoutLink', 'No Link'),
                "status": status,
                "reminder": "Pending",
                "start_dt": start_dt,
                "end_dt": end_dt
            })

        st.sidebar.markdown(f"**Current Time: ⏰ {datetime.now(tz.tzlocal()).strftime('%d %b %Y %I:%M %p %Z')}**")

        # st.sidebar.write("Meeting Times:")

        for idx, meeting in enumerate(meetings_data):
            cols = st.columns([4, 2, 1.5, 1.5, 1])
            # Update meeting status in real-time
            current_time = datetime.now(tz.tzlocal())

            if meeting['start_dt'] and meeting['end_dt']:
                # Convert meeting times to local timezone (redundant but safe)
                start_local = meeting['start_dt'].astimezone(tz.tzlocal())
                end_local = meeting['end_dt'].astimezone(tz.tzlocal())

                # Update status
                current_time = datetime.now(tz.tzlocal())
                if meeting['start_dt'] and meeting['end_dt']:
                    if current_time > meeting['end_dt']:
                        meetings_data[idx]['status'] = "Completed"
                    elif meeting['start_dt'] <= current_time <= meeting['end_dt']:
                        meetings_data[idx]['status'] = "In Progress"
                    else:
                        meetings_data[idx]['status'] = "Upcoming"

            with st.container():
                with cols[0]:
                    st.markdown(f"**{meeting['title']}**")

                with cols[1]:
                    st.markdown(f"{meeting['date']}  \n{meeting['time']}")

                with cols[2]:
                    status_class = meeting['status'].lower().replace(" ", "-")
                    st.markdown(
                        f"<div class='status-pill {status_class}'>{meeting['status']}</div>",
                        unsafe_allow_html=True
                    )

                with cols[3]:
                    if meeting.get('reminder', "Pending") == "Pending":  # Safe access
                        if meeting['status'] == "Upcoming":
                            if meeting['start_dt'] and is_reminder_time(meeting['start_dt']):
                                if st.session_state.phone_number:
                                    notifyuser(
                                        meeting['title'],
                                        f"{meeting['date']} {meeting['time']}",
                                        meeting['link'],
                                        st.session_state.phone_number
                                    )
                                    meetings_data[idx]['reminder'] = "Sent ✅"
                        st.markdown(meetings_data[idx]['reminder'])
                    else:
                        st.markdown("─")

                with cols[4]:
                    # Safely check for link and status
                    if meeting.get('link', 'No Link') != 'No Link' and meeting['status'] in ["Upcoming", "In Progress"]:
                        if st.button("Join", key=f"join_{idx}"):
                            webbrowser.open(meeting['link'])
                    else:
                        st.markdown("`─`")

        # Hidden Data Section
        st.subheader(" ", divider="blue")

        # Save credentials
        if not os.path.exists('token.pkl'):
            with open('token.pkl', 'wb') as f:
                pickle.dump(credentials, f)

        # New TODO List Section
        col1,col2,col3 = st.columns([2,3,4])
        col1.subheader("Meeting TODOs")

        if 'todos' not in st.session_state:
            st.session_state.todos = []
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = []

        if col3.button("Generate TODO"):
            with st.spinner("Checking for new recordings..."):
                try:
                    # Initialize Drive service
                    drive_service = build('drive', 'v3', credentials=credentials)

                    # Find Meet Recordings folder
                    folders = drive_service.files().list(
                        q="name='Meet Recordings' and mimeType='application/vnd.google-apps.folder'"
                    ).execute().get('files', [])

                    if not folders:
                        st.error("No Meet Recordings folder found")
                        return

                    folder_id = folders[0]['id']

                    # List video files in folder
                    files = drive_service.files().list(
                        q=f"'{folder_id}' in parents and (mimeType='video/mp4' or mimeType='video/webm')",
                        fields="files(id, name, createdTime)"
                    ).execute().get('files', [])

                    new_files = [f for f in files if f['id'] not in st.session_state.processed_files]

                    if not new_files:
                        st.info("No new recordings found")
                        return

                    for file in new_files:
                        st.write(f"Processing {file['name']} File from Storage")
                        file_name = file['name']
                        # Download file content
                        request = drive_service.files().get_media(fileId=file['id'])
                        file_content = request.execute()

                        # Upload to AssemblyAI
                        headers = {'authorization': st.secrets['ASSEMBLYAI_API_KEY']}
                        upload_response = requests.post(
                            'https://api.assemblyai.com/v2/upload',
                            headers=headers,
                            data=file_content
                        )

                        if upload_response.status_code != 200:
                            st.error(f"Upload failed for {file['name']}")
                            continue

                        upload_url = upload_response.json()['upload_url']

                        # Start transcription
                        transcript_response = requests.post(
                            'https://api.assemblyai.com/v2/transcript',
                            headers=headers,
                            json={'audio_url': upload_url}
                        )

                        if transcript_response.status_code != 200:
                            st.error(f"Transcription failed to start for {file['name']}")
                            continue

                        transcript_id = transcript_response.json()['id']

                        # Poll for completion
                        while True:
                            polling_response = requests.get(
                                f'https://api.assemblyai.com/v2/transcript/{transcript_id}',
                                headers=headers
                            )
                            status = polling_response.json()['status']

                            content = []

                            if status == 'completed':
                                transcript = polling_response.json().get('text', '')
                                content.append(transcript)
                                response = llm1.invoke(
                                    prompt_template.format(
                                        chat_history=[],  # This is where previous chat history goes
                                        input=content  # User query
                                    )
                                )
                                st.markdown(
                                        f"""
                                        <div style="
                                            background: linear-gradient(145deg, rgba(32,36,46,1) 0%, rgba(22,25,33,1) 100%);
                                            padding: 20px;
                                            margin: 15px 0;
                                            border-radius: 16px;
                                            border: 1px solid rgba(255,255,255,0.1);
                                            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
                                            position: relative;
                                            transition: transform 0.2s ease, box-shadow 0.2s ease;
                                            backdrop-filter: blur(4px);
                                        ">
                                            <div style="
                                                position: absolute;
                                                top: 0;
                                                left: 0;
                                                right: 0;
                                                height: 4px;
                                                background: linear-gradient(90deg, #6366f1 0%, #3b82f6 50%, #10b981 100%);
                                                border-radius: 16px 16px 0 0;
                                            "></div>
                                                {response.content}
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )

                                phone_number = st.session_state.phone_number
                                sendtodo(file_name,response.content,phone_number)
                                # Extract TODOs
                                #todos = re.findall(r'\b(TODO|Action Item):?\s*(.+?)(?=\n|$)', transcript, re.IGNORECASE)
                                #2)todos = re.findall(r'\b(?:TODO|Action Item):?\s*(.+)', transcript, re.IGNORECASE | re.MULTILINE)
                                todos = re.findall(r'(?:TODO|Action Item):?\s*(.+?)(?:\r?\n|$)', transcript,
                                                   re.IGNORECASE)
                                st.session_state.todos.extend([f"{todo[1]}" for todo in todos])
                                #st.session_state.processed_files.append(file['id'])
                                # st.success(f"Added {len(todos)} TODOs from {file['name']}")
                                break
                            elif status == 'error':
                                st.error(f"Transcription error for {file['name']}")
                                break
                            time.sleep(5)

                except Exception as e:
                    st.error(f"Error processing recordings: {str(e)}")

        # Display TODOs
        if st.session_state.todos:
            st.write("### Extracted Action Items")
            for i, todo in enumerate(st.session_state.todos, 1):
                cols = st.columns([1, 20])
                with cols[0]:
                    if st.checkbox("", key=f"done_{i}"):
                        st.session_state.todos[i - 1] = f"~~{todo}~~"
                with cols[1]:
                    st.markdown(st.session_state.todos[i - 1])
       


if __name__ == "__main__":
    main()
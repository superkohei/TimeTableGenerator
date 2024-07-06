import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
import io
import json

client = OpenAI(api_key=st.secrets['OPENAI_SECRET_KEY'])


def parse_input(input_text, sysprompt):

    try:
        # Request completion from OpenAI API
        response = client.chat.completions.create(model="gpt-3.5-turbo",
                                                  messages=[{
                                                      "role":
                                                      "system",
                                                      "content":
                                                      sysprompt
                                                  }, {
                                                      "role":
                                                      "user",
                                                      "content":
                                                      input_text
                                                  }],
                                                  max_tokens=500)
        #st.write(response)

        # Extract the content of the response

        lines = response.choices[
            0].message.content  #['choices'][0]['message']['content']
        # st.write("Raw API response:", lines)  # Debugging line

        # Print the response for debugging
        # print("Raw API response:", lines)

        # Attempt to parse the JSON-formatted string
        data = json.loads(lines)
        #st.write("Parsed JSON data:", data)  # Debugging line

        # Print the parsed JSON for debugging
        # print("Parsed JSON data:", data)

        # Convert to DataFrame
        df = pd.DataFrame(data['schedule'])

        # Display the DataFrame
        st.write("DataFrame:", df)  # Debugging line
        print("DataFrame:", df)

    except json.JSONDecodeError as e:
        st.error(
            "Failed to parse the schedule. Please check the input format.")
        st.write("JSONDecodeError:", str(e))  # Debugging line
        print("JSONDecodeError:", str(e))
        df = pd.DataFrame(columns=['Day', 'Time', 'Subject'])

    except Exception as e:
        st.error("An error occurred while processing the schedule.")
        st.write("Exception:", str(e))  # Debugging line
        print("Exception:", str(e))
        df = pd.DataFrame(columns=['Day', 'Time', 'Subject'])

    return df


example = """'''{
    "schedule": [
        {
            "Day": "Monday",
            "Time": "9 AM",
            "Subject": "Math"
        },
        {
            "Day": "Tuesday",
            "Time": "10 AM",
            "Subject": "Science"
        },
        {
            "Day": "Wednesday",
            "Time": "11 AM",
            "Subject": "History"
        }
    ]
}'''"""

sysprompt = f"""
You are a timetable planner. You will take in a user's input and return a timetable in JSON format with columns 'Day', 'Time', and 'Subject'. Give the respond as below: {example}
"""


# Function to generate timetable and detect clashes
def generate_timetable(schedule_df):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    times = sorted(schedule_df['Time'].unique())

    # Create a blank timetable
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.axis('tight')
    ax.axis('off')

    # Create table data structure
    table_data = [[''] + times]
    for day in days:
        row = [day]
        for time in times:
            subjects = schedule_df[(schedule_df['Day'] == day)
                                   & (schedule_df['Time'] == time)]
            if len(subjects) > 1:
                row.append('Clash: ' + ', '.join(subjects['Subject']))
            else:
                row.append(', '.join(subjects['Subject']))
        table_data.append(row)

    # Create the table
    table = ax.table(cellText=table_data,
                     loc='center',
                     cellLoc='center',
                     colWidths=[0.1] + [0.1] * len(times))

    # Add custom styling to the table
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(4, 2.5)

    for i in range(len(days) + 1):
        for j in range(len(times) + 1):
            cell = table[(i, j)]
            cell.set_fontsize(14)
            if i == 0 or j == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('#4CAF50')
            elif 'Clash' in cell.get_text().get_text():
                cell.set_facecolor('#FFCDD2')
            else:
                cell.set_facecolor('#FFF9C4')

    return fig


# Streamlit app
st.title('AI Timetable Generator')

# CSS to enlarge text area and button
st.markdown("""
    <style>
    .stTextArea, .stButton {
        font-size: 16px !important;
    }
    .stButton button {
        height: 3em;
        width: 100%;
        font-size: 18px;
    }
    </style>
    """,
            unsafe_allow_html=True)

input_text = st.text_area(
    'Enter your schedule:',
    'Monday, 9 AM, Math. Tuesday, 10 AM, Science. Wednesday, 11 AM, History.')

if st.button('Generate Timetable'):
    schedule_df = parse_input(input_text, sysprompt)
    st.write('Parsed Schedule:')
    st.write(schedule_df)

    if not schedule_df.empty and 'Day' in schedule_df.columns and 'Time' in schedule_df.columns and 'Subject' in schedule_df.columns:
        fig = generate_timetable(schedule_df)
        st.pyplot(fig)

        # Save timetable as image
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        st.download_button(label='Download Timetable as Image',
                           data=buf.getvalue(),
                           file_name='timetable.png',
                           mime='image/png')
    else:
        st.error(
            "The schedule data is not in the expected format. Please ensure it contains 'Day', 'Time', and 'Subject' columns."
        )

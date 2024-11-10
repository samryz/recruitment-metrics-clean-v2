import sqlite3
import pandas as pd
from datetime import datetime

def init_db():
    conn = sqlite3.connect('recruitment_data.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS recruitment_data (
            candidate_name TEXT,
            interview_date TEXT,
            interviewer TEXT,
            feedback_form TEXT,
            overall_score TEXT,
            candidate_origin TEXT,
            candidate_owner_name TEXT,
            posting_title TEXT,
            upload_date TEXT,
            upload_week TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_to_db(df):
    df_to_save = df.copy()
    
    # Rename columns
    column_mapping = {
        'Candidate Name': 'candidate_name',
        'Interview Date TZ': 'interview_date',
        'Interviewer': 'interviewer',
        'Feedback Form': 'feedback_form',
        'Overall Score': 'overall_score',
        'Candidate Origin': 'candidate_origin',
        'Candidate Owner Name': 'candidate_owner_name',
        'Posting Title': 'posting_title'
    }
    df_to_save = df_to_save.rename(columns=column_mapping)
    
    # Add tracking columns
    df_to_save['upload_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df_to_save['upload_week'] = pd.to_datetime(df_to_save['interview_date']).dt.strftime('%Y-W%V')
    
    conn = sqlite3.connect('recruitment_data.db')
    df_to_save.to_sql('recruitment_data', conn, if_exists='append', index=False)
    conn.close()
    
    return True, "Data saved successfully"

def load_from_db():
    conn = sqlite3.connect('recruitment_data.db')
    
    try:
        df = pd.read_sql_query("SELECT * FROM recruitment_data", conn)
        
        # Rename columns back
        column_mapping = {
            'candidate_name': 'Candidate Name',
            'interview_date': 'Interview Date TZ',
            'interviewer': 'Interviewer',
            'feedback_form': 'Feedback Form',
            'overall_score': 'Overall Score',
            'candidate_origin': 'Candidate Origin',
            'candidate_owner_name': 'Candidate Owner Name',
            'posting_title': 'Posting Title'
        }
        df = df.rename(columns=column_mapping)
        return df
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()
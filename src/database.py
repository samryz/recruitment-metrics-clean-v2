import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from supabase import create_client
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_supabase_client():
    """Create Supabase client with error handling"""
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
            
        # Create client with explicit database schema
        supabase = create_client(
            supabase_url=url,
            supabase_key=key
        )
        
        return supabase
        
    except Exception as e:
        raise ConnectionError(f"Connection error: {str(e)}")

def get_existing_records():
    """Get existing records from database"""
    try:
        supabase = create_supabase_client()
        response = supabase.table('recruitment_data').select('*').execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error getting existing records: {str(e)}")
        return pd.DataFrame()

def clean_for_json(value):
    """Clean values for JSON serialization"""
    if pd.isna(value):
        return None
    return str(value)

def save_to_db(df, supabase):
    """Save new records to database, avoiding duplicates"""
    try:
        print("\nStarting database save process...")
        print(f"Number of records in upload file: {len(df)}")
        
        df = df.copy()
        
        # Convert date with correct format for your input data
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'], format='%m/%d/%y %H:%M')
        
        # Create unique identifier for each record
        df['record_key'] = df.apply(
            lambda x: f"{x['Candidate Name']}_{x['Interview Date TZ'].strftime('%Y-%m-%d %H:%M')}_{x['Feedback Form']}", 
            axis=1
        )
        
        # Get existing records and create their keys
        existing_records = supabase.table('recruitment_data').select('*').execute()
        if existing_records and existing_records.data:
            existing_df = pd.DataFrame(existing_records.data)
            existing_df['record_key'] = existing_df.apply(
                lambda x: f"{x['candidate_name']}_{x['interview_date']}_{x['feedback_form']}", 
                axis=1
            )
            existing_keys = set(existing_df['record_key'])
            
            # Filter out records that already exist
            df = df[~df['record_key'].isin(existing_keys)]
        
        if len(df) == 0:
            print("No new records to add")
            return 0
            
        print(f"\nFound {len(df)} new records to add")
        
        # Process in chunks of 1000
        chunk_size = 1000
        records_inserted = 0
        
        for start_idx in range(0, len(df), chunk_size):
            chunk_df = df.iloc[start_idx:start_idx + chunk_size]
            
            records_to_insert = []
            for _, row in chunk_df.iterrows():
                record = {
                    'candidate_name': str(row['Candidate Name']),
                    'interview_date': row['Interview Date TZ'].strftime('%Y-%m-%d %H:%M:%S'),
                    'feedback_form': str(row['Feedback Form']),
                    'interviewer': str(row['Interviewer']),
                    'overall_score': float(row['Overall Score']) if pd.notnull(row['Overall Score']) else None,
                    'candidate_origin': str(row['Candidate Origin']),
                    'candidate_owner_name': str(row['Candidate Owner Name']) if pd.notnull(row.get('Candidate Owner Name')) else None,
                    'posting_title': str(row['Posting Title']) if pd.notnull(row.get('Posting Title')) else None
                }
                records_to_insert.append(record)
            
            if records_to_insert:
                print(f"\nInserting chunk of {len(records_to_insert)} records")
                result = supabase.table('recruitment_data').insert(records_to_insert).execute()
                records_inserted += len(records_to_insert)
        
        print(f"\nSuccessfully inserted {records_inserted} records")
        return records_inserted
        
    except Exception as e:
        print(f"Error saving to database: {str(e)}")
        raise e

def get_record_count():
    """Get current record count"""
    try:
        supabase = create_supabase_client()
        response = supabase.table('recruitment_data').select('*', count='exact').execute()
        return response.count
    except Exception as e:
        print(f"Error getting record count: {str(e)}")
        return 0
import pandas as pd
from datetime import datetime, timedelta

def process_ats_data(df):
    """Process the ATS data and calculate metrics"""
    # Convert date column if not already datetime
    if not pd.api.types.is_datetime64_any_dtype(df['Interview Date TZ']):
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    
    # Create pass/fail column
    df['Interview Result'] = df['Overall Score'].apply(
        lambda x: 'Pass' if x in [3, 4] else 'Fail' if x in [1, 2] else 'Unknown'
    )
    
    # Global metrics
    global_metrics = {
        'total_onsite_interviews': len(df[df['Feedback Form'] == 'On-site interview']),
        'total_sourced': len(df[df['Candidate Origin'] == 'Sourced']),
        'total_applied': len(df[df['Candidate Origin'] == 'Applied'])
    }
    
    # Filter for recruiter screens only
    recruiter_screens = df[df['Feedback Form'] == 'Recruiter Screen']
    
    # Calculate recruiter metrics
    recruiter_metrics = {}
    for recruiter in df['Candidate Owner Name'].unique():
        recruiter_data = recruiter_screens[recruiter_screens['Candidate Owner Name'] == recruiter]
        
        metrics = {
            'total_screens': len(recruiter_data),
            'passed_screens': len(recruiter_data[recruiter_data['Interview Result'] == 'Pass']),
            'failed_screens': len(recruiter_data[recruiter_data['Interview Result'] == 'Fail']),
            'pass_rate': round(len(recruiter_data[recruiter_data['Interview Result'] == 'Pass']) / 
                             len(recruiter_data) * 100 if len(recruiter_data) > 0 else 0, 2)
        }
        recruiter_metrics[recruiter] = metrics
    
    # Convert to DataFrame for easier visualization
    recruiter_df = pd.DataFrame.from_dict(recruiter_metrics, orient='index')
    
    metrics = {
        'recruiter_performance': recruiter_df,
        'total_recruiter_screens': len(recruiter_screens),
        'total_passed': len(recruiter_screens[recruiter_screens['Interview Result'] == 'Pass']),
        'total_failed': len(recruiter_screens[recruiter_screens['Interview Result'] == 'Fail']),
        'overall_pass_rate': round(len(recruiter_screens[recruiter_screens['Interview Result'] == 'Pass']) / 
                                 len(recruiter_screens) * 100 if len(recruiter_screens) > 0 else 0, 2),
        'global_metrics': global_metrics
    }
    
    return metrics

def get_time_period_data(df, period):
    """Filter data for specific time periods"""
    now = pd.Timestamp.now()
    
    if period == "All Time":
        return df
    elif period == "This Week":
        start_date = now - timedelta(days=now.weekday())
        return df[df['Interview Date TZ'] >= start_date]
    elif period == "Last Week":
        start_date = now - timedelta(days=now.weekday() + 7)
        end_date = start_date + timedelta(days=7)
        return df[(df['Interview Date TZ'] >= start_date) & (df['Interview Date TZ'] < end_date)]
    elif period == "This Month":
        start_date = now.replace(day=1)
        return df[df['Interview Date TZ'] >= start_date]
    elif period == "Last Month":
        last_month = now - pd.DateOffset(months=1)
        start_date = last_month.replace(day=1)
        end_date = now.replace(day=1)
        return df[(df['Interview Date TZ'] >= start_date) & (df['Interview Date TZ'] < end_date)]
    
    return df

def calculate_period_comparison(current_df, previous_df):
    """Calculate metrics comparison between two periods"""
    current_metrics = process_ats_data(current_df)
    previous_metrics = process_ats_data(previous_df)
    
    comparison = {
        'screens_change': calculate_percentage_change(
            current_metrics['total_recruiter_screens'],
            previous_metrics['total_recruiter_screens']
        ),
        'pass_rate_change': calculate_percentage_change(
            current_metrics['overall_pass_rate'],
            previous_metrics['overall_pass_rate']
        ),
        'onsite_change': calculate_percentage_change(
            current_metrics['global_metrics']['total_onsite_interviews'],
            previous_metrics['global_metrics']['total_onsite_interviews']
        )
    }
    
    return comparison

def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100
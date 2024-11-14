import pandas as pd
from datetime import datetime
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def validate_metrics_data(df):
    """Validate data for metrics calculations"""
    try:
        required_columns = [
            'Interviewer', 
            'Feedback Form', 
            'Overall Score',
            'Interview Date TZ',
            'Candidate Name',
            'Candidate Origin'
        ]
        
        # Map database column names to expected names
        column_mapping = {
            'interviewer': 'Interviewer',
            'feedback_form': 'Feedback Form',
            'overall_score': 'Overall Score',
            'interview_date': 'Interview Date TZ',
            'candidate_name': 'Candidate Name',
            'candidate_origin': 'Candidate Origin'
        }
        
        # Rename columns if they exist in database format
        df_temp = df.copy()
        df_temp = df_temp.rename(columns=column_mapping)
        
        missing_cols = [col for col in required_columns if col not in df_temp.columns]
        
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}"
            
        if df_temp.empty:
            return False, "No data available for metrics calculation"
            
        return True, None
    except Exception as e:
        return False, f"Error validating metrics data: {str(e)}"

@st.cache_data(ttl=3600)
def get_recruiter_screen_metrics(df, weeks_to_show=4):
    """Calculate recruiter screen metrics for the last n weeks"""
    try:
        # Ensure datetime
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
        
        # Filter recruiter screens
        recruiter_screens = df[
            df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False) &
            ~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])
        ].copy()
        
        if recruiter_screens.empty:
            print("No recruiter screens found")
            return pd.DataFrame()
            
        # Get latest weeks
        latest_weeks = sorted(recruiter_screens['Week'].unique())[-weeks_to_show:]
        
        if not latest_weeks:
            print("No weeks found")
            return pd.DataFrame()
            
        # Calculate metrics
        weekly_metrics = recruiter_screens[
            recruiter_screens['Week'].isin(latest_weeks)
        ].groupby(['Week', 'Interviewer']).agg({
            'Candidate Name': 'count',
            'Overall Score': lambda x: sum(pd.to_numeric(x, errors='coerce') >= 3)
        }).reset_index()
        
        weekly_metrics.columns = ['Week', 'Recruiter', 'Total Screens', 'Passes']
        weekly_metrics['Pass Rate'] = (
            weekly_metrics['Passes'] / 
            weekly_metrics['Total Screens'] * 
            100
        ).round(1)
        
        return weekly_metrics
        
    except Exception as e:
        print(f"Error in get_recruiter_screen_metrics: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_onsite_interview_metrics(df, weeks_to_show=4):
    """Calculate onsite interview metrics for Sam and Jordan"""
    df = df.copy()
    
    # Ensure dates are datetime
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    # Filter for onsite interviews
    onsite_interviews = df[
        df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])
    ].drop_duplicates(subset=['Candidate Name', 'Interview Date TZ', 'Interviewer'])
    
    # Get latest weeks
    latest_weeks = sorted(
        df['Week'].unique(),
        key=lambda x: datetime.strptime(x + '-1', '%Y-W%W-%w')
    )[-weeks_to_show:]
    
    # Calculate metrics
    metrics = onsite_interviews[
        onsite_interviews['Week'].isin(latest_weeks)
    ].groupby(['Week', 'Interviewer']).agg({
        'Candidate Name': 'nunique'
    }).reset_index()
    
    metrics.columns = ['Week', 'Interviewer', 'Total Onsites']
    return metrics

@st.cache_data(ttl=3600)
def get_onsite_conversion_metrics(df, weeks_to_show=4):
    """Calculate onsite interview conversion rates per recruiter"""
    df = df.copy()
    
    # Ensure dates are datetime
    df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
    df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
    
    # Get latest weeks
    latest_weeks = sorted(
        df['Week'].unique(),
        key=lambda x: datetime.strptime(x + '-1', '%Y-W%W-%w')
    )[-weeks_to_show:]
    
    # Get all recruiters
    recruiters = df[
        (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)) &
        ~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])
    ]['Interviewer'].unique()
    
    conversion_metrics = []
    for week in latest_weeks:
        week_data = df[df['Week'] == week]
        onsite_interviews = week_data[
            week_data['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])
        ]
        
        for recruiter in recruiters:
            recruiter_candidates = df[
                (df['Interviewer'] == recruiter) &
                (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False))
            ]['Candidate Name'].unique()
            
            total_onsites = len(onsite_interviews[
                onsite_interviews['Candidate Name'].isin(recruiter_candidates)
            ])
            
            total_screens = len(recruiter_candidates)
            conversion = (total_onsites / total_screens * 100) if total_screens > 0 else 0
            
            conversion_metrics.append({
                'Week': week,
                'Recruiter': recruiter,
                'Onsites': total_onsites,
                'Conversion': conversion
            })
    
    return pd.DataFrame(conversion_metrics)

@st.cache_data(ttl=3600)
def get_source_metrics(df, weeks_to_show=4):
    """Calculate applied vs sourced ratios"""
    # Your existing function code

@st.cache_data(ttl=3600)
def get_time_to_hire_metrics(df, weeks_to_show=4):
    """Calculate time between recruiter screen and onsite"""
    # Your existing function code

@st.cache_data(ttl=3600)
def get_quality_metrics(df, weeks_to_show=4):
    """Calculate quality metrics for recruiters"""
    # Your existing function code

@st.cache_data(ttl=3600)
def get_monday_date(df):
    """Get the Monday date for the latest week with data"""
    try:
        # Convert to datetime if not already
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        
        # Get the latest date with data
        latest_date = df['Interview Date TZ'].max()
        
        if pd.isnull(latest_date):
            return None
            
        # Calculate the Monday of that week
        monday_date = latest_date - pd.Timedelta(days=latest_date.weekday())
        
        # Format as string
        return monday_date.strftime('%B %d, %Y')
        
    except Exception as e:
        print(f"Error getting Monday date: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def get_star_recruiter(metrics_df):
    """Returns the recruiter with the most screens"""
    # Your existing function code

def get_recruiter_emoji(recruiter, star_recruiter):
    """Get emoji for recruiter based on performance"""
    try:
        if recruiter == star_recruiter:
            return "⭐"  # Star for top performer
        return "👩"  # Woman emoji for all other recruiters
        
    except Exception as e:
        print(f"Error getting recruiter emoji: {str(e)}")
        return "📊"  # Default emoji if something goes wrong

@st.cache_data(ttl=3600)
def get_weekly_source_breakdown(df, weeks_to_show=16):
    """Get weekly breakdown of candidate sources for the last N weeks"""
    print("\nDEBUG: In get_weekly_source_breakdown")
    print(f"Input data date range: {df['Interview Date TZ'].min()} to {df['Interview Date TZ'].max()}")
    print(f"Unique weeks: {sorted(df['Interview Date TZ'].dt.isocalendar().week.unique())}")
    
    try:
        df = df.copy()
        
        # Print date range to debug
        print("\nDATE RANGE CHECK:")
        print(f"Earliest date: {df['Interview Date TZ'].min()}")
        print(f"Latest date: {df['Interview Date TZ'].max()}")
        print(f"Total records: {len(df)}")
        
        # Get the most recent date and calculate start date
        most_recent_date = df['Interview Date TZ'].max()
        start_date = most_recent_date - pd.Timedelta(weeks=weeks_to_show)
        
        # Filter to our date range
        df = df[df['Interview Date TZ'] >= start_date]
        df['Week'] = df['Interview Date TZ'].dt.strftime('2024-W%V')
        
        # Print week numbers to debug
        print("\nWeeks in data:")
        print(df['Week'].value_counts().sort_index())
        
        # Filter for recruiter screens
        screens = df[
            df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)
        ].copy()
        
        # Print recruiter screen counts by week
        print("\nRecruiter screens by week:")
        print(screens['Week'].value_counts().sort_index())
        
        # Get all weeks in our range
        all_weeks = sorted(screens['Week'].unique())
        
        weekly_data = []
        for week in all_weeks:
            week_data = screens[screens['Week'] == week]
            sources = week_data['Candidate Origin'].fillna('Unknown').str.lower()
            
            applied = len(sources[
                sources.str.contains('applied|application|direct', na=False)
            ])
            sourced = len(sources[
                sources.str.contains('sourced|sourcing|linkedin|outbound', na=False)
            ])
            referred = len(sources[
                sources.str.contains('referred|referral|internal', na=False)
            ])
            
            total = len(week_data)
            
            weekly_data.append({
                'Week': week,
                'Applied': applied,
                'Sourced': sourced,
                'Referred': referred,
                'Total': total
            })
        
        result_df = pd.DataFrame(weekly_data)
        
        # Print final results to debug
        print("\nFinal weekly totals:")
        print(result_df.sort_values('Week')[['Week', 'Total', 'Applied', 'Sourced', 'Referred']])
        
        return result_df
        
    except Exception as e:
        print(f"Error getting source breakdown: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_recruiter_performance_last_week(df):
    """Get detailed recruiter performance metrics for the last week"""
    try:
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
        
        # Get the last week in the data
        last_week = df['Week'].max()
        
        # Filter for recruiters (excluding Sam and Jordan)
        recruiters = df[~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])]['Interviewer'].unique()
        
        performance_data = []
        for recruiter in recruiters:
            # Get recruiter screens for last week
            recruiter_screens = df[
                (df['Week'] == last_week) &
                (df['Interviewer'] == recruiter) &
                (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False))
            ]
            
            # Calculate screen metrics
            total_screens = len(recruiter_screens)
            screen_passes = sum(pd.to_numeric(recruiter_screens['Overall Score'], errors='coerce') >= 3)
            screen_pass_rate = (screen_passes / total_screens * 100) if total_screens > 0 else 0
            
            # Get onsite interviews for recruiter's candidates
            recruiter_candidates = recruiter_screens['Candidate Name'].unique()
            onsite_interviews = df[
                (df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])) &
                (df['Candidate Name'].isin(recruiter_candidates))
            ]
            
            total_onsites = len(onsite_interviews)
            onsite_passes = sum(pd.to_numeric(onsite_interviews['Overall Score'], errors='coerce') >= 3)
            onsite_pass_rate = (onsite_passes / total_onsites * 100) if total_onsites > 0 else 0
            
            performance_data.append({
                'Recruiter': recruiter,
                'Screens': total_screens,
                'Screen Pass Rate': round(screen_pass_rate, 1),
                'Onsites': total_onsites,
                'Onsite Pass Rate': round(onsite_pass_rate, 1)
            })
            
        return pd.DataFrame(performance_data)
    except Exception as e:
        print(f"Error in recruiter performance: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_recruiter_performance_metrics(df):
    """Calculate performance metrics for each recruiter"""
    try:
        metrics = {}
        
        # Filter for recruiter screens only
        recruiter_screens = df[
            df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False) &
            ~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])
        ]
        
        # Get unique recruiters
        recruiters = recruiter_screens['Interviewer'].unique()
        
        for recruiter in recruiters:
            recruiter_data = recruiter_screens[recruiter_screens['Interviewer'] == recruiter]
            
            if not recruiter_data.empty:
                # Calculate metrics
                screens = len(recruiter_data)
                pass_rate = (pd.to_numeric(recruiter_data['Overall Score'], 
                                         errors='coerce').fillna(0) >= 3).mean() * 100
                
                # Calculate time to hire (average days between screens)
                sorted_dates = pd.to_datetime(recruiter_data['Interview Date TZ']).sort_values()
                time_to_hire = sorted_dates.diff().mean().total_seconds() / (24 * 3600)  # Convert to days
                
                metrics[recruiter] = {
                    'screens': screens,
                    'pass_rate': pass_rate if not pd.isna(pass_rate) else 0,
                    'time_to_hire': time_to_hire if not pd.isna(time_to_hire) else 0
                }
            
        return metrics
        
    except Exception as e:
        print(f"Error calculating recruiter metrics: {str(e)}")
        return {}

@st.cache_data(ttl=3600)
def get_onsite_metrics_by_recruiter(df, weeks_to_show):
    """Calculate weekly onsite interviews by original recruiter"""
    try:
        df = df.copy()
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
        
        # Get latest weeks
        latest_weeks = sorted(df['Week'].unique())[-weeks_to_show:]
        
        # Get recruiters (excluding Sam and Jordan)
        recruiters = df[
            (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)) & 
            (~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner']))
        ]['Interviewer'].unique()
        
        # Create base dataframe with all week/recruiter combinations
        week_recruiter_combos = pd.MultiIndex.from_product(
            [latest_weeks, recruiters],
            names=['Week', 'Recruiter']
        ).to_frame(index=False)
        
        # Get onsite interviews
        onsite_data = df[
            (df['Week'].isin(latest_weeks)) &
            (df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner']))
        ].copy()
        
        # Calculate onsites by week and recruiter
        weekly_onsites = []
        for week in latest_weeks:
            week_onsites = onsite_data[onsite_data['Week'] == week]
            for recruiter in recruiters:
                recruiter_candidates = df[
                    (df['Interviewer'] == recruiter) &
                    (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False))
                ]['Candidate Name'].unique()
                
                onsite_count = len(week_onsites[
                    week_onsites['Candidate Name'].isin(recruiter_candidates)
                ])
                
                weekly_onsites.append({
                    'Week': week,
                    'Recruiter': recruiter,
                    'Onsites': onsite_count
                })
        
        # Create final dataframe
        onsite_df = pd.DataFrame(weekly_onsites)
        full_onsite_data = week_recruiter_combos.merge(
            onsite_df,
            on=['Week', 'Recruiter'],
            how='left'
        ).fillna(0)
        
        return full_onsite_data
        
    except Exception as e:
        print(f"Error in onsite metrics by recruiter: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_monday_date(df):
    """Get Monday date for the most recent week"""
    try:
        latest_date = pd.to_datetime(df['Interview Date TZ']).max()
        monday = latest_date - pd.Timedelta(days=latest_date.weekday())
        return monday.strftime('%B %d, %Y')
    except Exception as e:
        print(f"Error getting Monday date: {str(e)}")
        return "N/A"

@st.cache_data(ttl=3600)
def get_star_recruiter(metrics_df):
    """Determine star recruiter based on total screens"""
    try:
        if metrics_df.empty:
            return None
            
        # Group by recruiter and sum screens
        recruiter_totals = metrics_df.groupby('Recruiter')['Total Screens'].sum()
        
        # Get recruiter with most screens
        star_recruiter = recruiter_totals.idxmax()
        return star_recruiter
        
    except Exception as e:
        print(f"Error getting star recruiter: {str(e)}")
        return None

def get_recruiter_emoji(recruiter, star_recruiter):
    """Get emoji for recruiter based on performance"""
    try:
        if recruiter == star_recruiter:
            return "⭐"  # Star for top performer
        return "👩"  # Woman emoji for all other recruiters
        
    except Exception as e:
        print(f"Error getting recruiter emoji: {str(e)}")
        return "📊"  # Default emoji if something goes wrong

@st.cache_data(ttl=3600)
def get_onsite_conversion_metrics(df, weeks_to_show=4):
    """Calculate onsite conversion rates per recruiter"""
    try:
        df = df.copy()
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        df['Week'] = df['Interview Date TZ'].dt.strftime('%Y-W%V')
        
        # Get latest weeks
        latest_weeks = sorted(df['Week'].unique())[-weeks_to_show:]
        
        # Get recruiters (excluding Sam and Jordan)
        recruiters = df[
            (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)) & 
            (~df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner']))
        ]['Interviewer'].unique()
        
        conversion_metrics = []
        
        for week in latest_weeks:
            week_data = df[df['Week'] == week]
            
            for recruiter in recruiters:
                # Get candidates screened by this recruiter
                recruiter_candidates = df[
                    (df['Interviewer'] == recruiter) &
                    (df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False))
                ]['Candidate Name'].unique()
                
                # Get onsite interviews for these candidates
                onsite_interviews = week_data[
                    (week_data['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])) &
                    (week_data['Candidate Name'].isin(recruiter_candidates))
                ]
                
                total_onsites = len(onsite_interviews)
                
                # Calculate conversion rate
                recruiter_screens = week_data[
                    (week_data['Interviewer'] == recruiter) &
                    (week_data['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False))
                ]
                
                total_screens = len(recruiter_screens)
                conversion_rate = (total_onsites / total_screens * 100) if total_screens > 0 else 0
                
                conversion_metrics.append({
                    'Week': week,
                    'Recruiter': recruiter,
                    'Onsites': total_onsites,
                    'Conversion': round(conversion_rate, 1)
                })
        
        return pd.DataFrame(conversion_metrics)
        
    except Exception as e:
        print(f"Error calculating conversion metrics: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_time_to_hire_metrics(df):
    """Calculate average time to hire"""
    try:
        df = df.copy()
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        
        # Get candidates who had both recruiter screen and onsite
        recruiter_screens = df[
            df['Feedback Form'].str.contains('Recruiter Screen', case=False, na=False)
        ][['Candidate Name', 'Interview Date TZ']].copy()
        
        onsite_interviews = df[
            df['Interviewer'].isin(['Sam Nadler', 'Jordan Metzner'])
        ][['Candidate Name', 'Interview Date TZ']].copy()
        
        # Merge to get time differences
        merged = pd.merge(
            recruiter_screens,
            onsite_interviews,
            on='Candidate Name',
            suffixes=('_screen', '_onsite')
        )
        
        # Calculate days between screen and onsite
        merged['days_to_hire'] = (
            merged['Interview Date TZ_onsite'] - 
            merged['Interview Date TZ_screen']
        ).dt.total_seconds() / (24 * 3600)
        
        # Return average days to hire
        return merged['days_to_hire'].mean()
        
    except Exception as e:
        print(f"Error calculating time to hire: {str(e)}")
        return None

def get_latest_week_data(df):
    """Get data for the most recent week only"""
    try:
        df = df.copy()
        df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
        latest_date = df['Interview Date TZ'].max()
        week_start = latest_date - pd.Timedelta(days=latest_date.weekday())
        
        # Filter to just this week's data
        latest_data = df[df['Interview Date TZ'] >= week_start]
        
        print(f"\nLatest week stats:")
        print(f"Week starting: {week_start.strftime('%Y-%m-%d')}")
        print(f"Total records: {len(latest_data)}")
        print(f"Unique candidates: {latest_data['Candidate Name'].nunique()}")
        
        return latest_data
        
    except Exception as e:
        print(f"Error getting latest week data: {str(e)}")
        return pd.DataFrame()

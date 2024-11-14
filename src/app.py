import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from database import save_to_db, get_record_count, create_supabase_client
from metrics import (
    validate_metrics_data,
    get_recruiter_screen_metrics,
    get_onsite_interview_metrics,
    get_onsite_conversion_metrics,
    get_source_metrics,
    get_time_to_hire_metrics,
    get_quality_metrics,
    get_monday_date,
    get_star_recruiter,
    get_recruiter_emoji,
    get_weekly_source_breakdown,
    get_recruiter_performance_metrics,
    get_onsite_metrics_by_recruiter
)

# Must be the first Streamlit command
st.set_page_config(layout="wide")

def handle_file_upload(uploaded_file):
    """Handle file upload and save to database"""
    try:
        # Check if we're already processing this file
        file_name = uploaded_file.name
        if 'last_uploaded_file' in st.session_state and st.session_state['last_uploaded_file'] == file_name:
            return
        
        # Create Supabase client
        supabase = create_supabase_client()
        
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Save to database
        records_added = save_to_db(df, supabase)
        
        if records_added > 0:
            # Clear all caches
            st.cache_data.clear()
            st.cache_resource.clear()
            
            # Store the file name in session state
            st.session_state['last_uploaded_file'] = file_name
            st.session_state['refresh_required'] = True
            
            st.success(f"Successfully added {records_added} new records to the database!")
            time.sleep(1)  # Brief pause to ensure cache is cleared
            st.rerun()  # Force a complete page refresh
        else:
            st.info("No new records to add. Data may already exist in the database.")
            
    except Exception as e:
        st.error(f"Upload error: {str(e)}")

@st.cache_data(ttl=30)
def get_current_data():
    """Get current data from database"""
    try:
        record_count = get_record_count()
        print(f"\nDEBUG: Current record count: {record_count}")
        
        supabase = create_supabase_client()
        
        # Fetch all records in chunks
        all_data = []
        chunk_size = 1000
        offset = 0
        
        while True:
            response = supabase.table('recruitment_data')\
                .select('*')\
                .order('interview_date', desc=True)\
                .range(offset, offset + chunk_size - 1)\
                .execute()
                
            print(f"DEBUG: Fetched chunk of size: {len(response.data) if response.data else 0}")
            
            if not response.data:
                break
                
            all_data.extend(response.data)
            if len(response.data) < chunk_size:
                break
                
            offset += chunk_size
        
        print(f"DEBUG: Total records fetched: {len(all_data)}")
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Map columns from database names back to original names
            column_mapping = {
                'candidate_name': 'Candidate Name',
                'interview_date': 'Interview Date TZ',
                'feedback_form': 'Feedback Form',
                'interviewer': 'Interviewer',
                'overall_score': 'Overall Score',
                'candidate_origin': 'Candidate Origin'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Convert date back to datetime
            df['Interview Date TZ'] = pd.to_datetime(df['Interview Date TZ'])
            
            print("\nDEBUG: Week distribution:")
            print(df['Interview Date TZ'].dt.isocalendar().week.value_counts().sort_index())
            
            print("\nLoaded data info:")
            print(f"Total records: {len(df)}")
            print("Columns:", df.columns.tolist())
            print("\nDEBUG: Date range in data:")
            print(f"Earliest date: {df['Interview Date TZ'].min()}")
            print(f"Latest date: {df['Interview Date TZ'].max()}")
            print(f"Unique weeks: {sorted(df['Interview Date TZ'].dt.isocalendar().week.unique())}")
            
            return df
            
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Data fetch error: {str(e)}")
        return pd.DataFrame()

def render_metrics_dashboard(df):
    """Render the metrics dashboard with all sections"""
    try:
        monday_str = get_monday_date(df)
        
        # Source Distribution Section
        st.markdown(
            f"<h2 style='color: #0066cc;'>Source Distribution (Week of {monday_str})</h2>", 
            unsafe_allow_html=True
        )
        
        # Get source distribution data
        source_data = get_weekly_source_breakdown(df)
        if not source_data.empty:
            fig_source = go.Figure()
            
            # Add bars in correct order with matching colors
            fig_source.add_trace(go.Bar(
                name='Applied',
                x=source_data['Week'],
                y=source_data['Applied'],
                marker_color='#0066CC'  # Dark blue
            ))
            
            fig_source.add_trace(go.Bar(
                name='Sourced',
                x=source_data['Week'],
                y=source_data['Sourced'],
                marker_color='#99CCFF'  # Light blue
            ))
            
            fig_source.add_trace(go.Bar(
                name='Referred',
                x=source_data['Week'],
                y=source_data['Referred'],
                marker_color='#FF4D4D'  # Red
            ))
            
            # Add total line
            fig_source.add_trace(go.Scatter(
                name='Total Trend',
                x=source_data['Week'],
                y=source_data['Total'],
                mode='lines+markers',
                line=dict(color='#FF0000', width=2),
                marker=dict(size=6),
            ))
            
            # Update layout
            fig_source.update_layout(
                title='Weekly Candidate Source Distribution',
                barmode='stack',
                height=400,
                margin=dict(t=40, b=40),
                plot_bgcolor='white',
                paper_bgcolor='white',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    title='Week',
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)'
                ),
                yaxis=dict(
                    title='Number of Candidates',
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.1)'
                )
            )
            
            # Add the chart to the dashboard
            st.plotly_chart(fig_source, use_container_width=True)
        else:
            st.info("No source distribution data available")

        # Recruiter Performance Section
        st.markdown(
            f"<h2 style='color: #0066cc;'>Recruiter Performance (Week of {monday_str})</h2>", 
            unsafe_allow_html=True
        )
        
        # Overall Performance
        st.markdown("<h3>Overall Performance</h3>", unsafe_allow_html=True)
        
        try:
            current_metrics = get_recruiter_screen_metrics(df, weeks_to_show=1)
            prev_metrics = get_recruiter_screen_metrics(df, weeks_to_show=2)
            onsite_metrics = get_onsite_conversion_metrics(df, weeks_to_show=1)
            prev_onsite_metrics = get_onsite_conversion_metrics(df, weeks_to_show=2)
            
            if not current_metrics.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_screens = current_metrics['Total Screens'].sum()
                    prev_week_screens = prev_metrics['Total Screens'].sum() - total_screens
                    st.metric(
                        "Total Screens This Week",
                        f"{total_screens}",
                        f"{total_screens - prev_week_screens:+d} vs prev week"
                    )
                
                with col2:
                    avg_pass_rate = current_metrics['Pass Rate'].mean()
                    prev_week_pass_rate = prev_metrics['Pass Rate'].mean()
                    st.metric(
                        "Average Pass Rate",
                        f"{avg_pass_rate:.1f}%",
                        f"{avg_pass_rate - prev_week_pass_rate:+.1f}% vs prev week"
                    )
                
                with col3:
                    total_onsites = onsite_metrics['Onsites'].sum()
                    prev_week_onsites = prev_onsite_metrics['Onsites'].sum() - total_onsites
                    st.metric(
                        "Total Onsite Interviews",
                        f"{total_onsites}",
                        f"{total_onsites - prev_week_onsites:+d} vs prev week"
                    )
                
                with col4:
                    conversion_rate = onsite_metrics['Conversion'].mean()
                    prev_week_conversion = prev_onsite_metrics['Conversion'].mean()
                    st.metric(
                        "Avg Onsite Conversion",
                        f"{conversion_rate:.1f}%",
                        f"{conversion_rate - prev_week_conversion:+.1f}% vs prev week"
                    )
            else:
                st.info("No metrics available for the current period")
                
        except Exception as e:
            st.error(f"Error rendering overall metrics: {str(e)}")

        # Individual Performance with star recruiter
        st.markdown("<h3>Individual Performance</h3>", unsafe_allow_html=True)
        
        try:
            star_recruiter = get_star_recruiter(current_metrics)
            
            for recruiter in current_metrics['Recruiter'].unique():
                # Get metrics for this recruiter
                current_data = current_metrics[current_metrics['Recruiter'] == recruiter]
                prev_data = prev_metrics[
                    (prev_metrics['Recruiter'] == recruiter) & 
                    (prev_metrics['Week'] != current_metrics['Week'].iloc[0])
                ]
                
                current_onsite = onsite_metrics[onsite_metrics['Recruiter'] == recruiter]['Onsites'].sum()
                prev_onsite = prev_onsite_metrics[
                    (prev_onsite_metrics['Recruiter'] == recruiter) & 
                    (prev_onsite_metrics['Week'] != current_metrics['Week'].iloc[0])
                ]['Onsites'].sum()
                
                current_conv = onsite_metrics[onsite_metrics['Recruiter'] == recruiter]['Conversion'].mean()
                prev_conv = prev_onsite_metrics[
                    (prev_onsite_metrics['Recruiter'] == recruiter) & 
                    (prev_onsite_metrics['Week'] != current_metrics['Week'].iloc[0])
                ]['Conversion'].mean()
                
                # Create row for each recruiter
                emoji = get_recruiter_emoji(recruiter, star_recruiter)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"### {emoji} {recruiter}")
                    current_screens = current_data['Total Screens'].iloc[0]
                    prev_screens = prev_data['Total Screens'].iloc[0] if not prev_data.empty else 0
                    st.metric(
                        "Screens",
                        current_screens,
                        f"{current_screens - prev_screens:+d} vs prev week"
                    )
                
                with col2:
                    current_pass = current_data['Pass Rate'].iloc[0]
                    prev_pass = prev_data['Pass Rate'].iloc[0] if not prev_data.empty else 0
                    st.metric(
                        "Pass Rate",
                        f"{current_pass:.1f}%",
                        f"{current_pass - prev_pass:+.1f}% vs prev week"
                    )
                
                with col3:
                    st.metric(
                        "Onsite Interviews",
                        current_onsite,
                        f"{current_onsite - prev_onsite:+d} vs prev week"
                    )
                
                with col4:
                    st.metric(
                        "Onsite Conversion",
                        f"{current_conv:.1f}%" if not pd.isna(current_conv) else "0.0%",
                        f"{current_conv - prev_conv:+.1f}% vs prev week" if not pd.isna(current_conv - prev_conv) else "0.0%"
                    )
                
                # Add a small space between recruiters
                st.markdown("<br>", unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error rendering individual metrics: {str(e)}")

        # Trend Analysis Section
        st.markdown("<h2 style='color: #0066cc;'>Trend Analysis</h2>", unsafe_allow_html=True)
        
        weeks_to_show = st.selectbox(
            "Select Time Period",
            options=[4, 8, 12],
            format_func=lambda x: f"Last {x} Weeks",
            key="trend_weeks"
        )

        # Weekly Screens by Recruiter
        trend_metrics = get_recruiter_screen_metrics(df, weeks_to_show=weeks_to_show)
        if not trend_metrics.empty:
            fig_screens = go.Figure()
            for recruiter in trend_metrics['Recruiter'].unique():
                recruiter_data = trend_metrics[trend_metrics['Recruiter'] == recruiter]
                fig_screens.add_trace(go.Scatter(
                    x=recruiter_data['Week'],
                    y=recruiter_data['Total Screens'],
                    name=recruiter,
                    mode='lines+markers'
                ))
            
            fig_screens.update_layout(
                title='Weekly Screens by Recruiter',
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="right",
                    x=1.15
                )
            )
            st.plotly_chart(fig_screens, use_container_width=True, key="screens_trend")

        # Weekly Onsite Interviews by Recruiter
        onsite_data = get_onsite_metrics_by_recruiter(df, weeks_to_show)
        if not onsite_data.empty:
            fig_recruiter_onsites = go.Figure()
            for recruiter in onsite_data['Recruiter'].unique():
                recruiter_data = onsite_data[onsite_data['Recruiter'] == recruiter]
                fig_recruiter_onsites.add_trace(go.Scatter(
                    x=recruiter_data['Week'],
                    y=recruiter_data['Onsites'],
                    name=recruiter,
                    mode='lines+markers'
                ))
            
            fig_recruiter_onsites.update_layout(
                title=f'Weekly Onsite Interviews by Recruiter (Last {weeks_to_show} Weeks)',
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="right",
                    x=1.15
                )
            )
            st.plotly_chart(fig_recruiter_onsites, use_container_width=True, key="recruiter_onsites_trend")

        # Weekly Onsite Interviews (Sam & Jordan)
        onsite_trend = get_onsite_interview_metrics(df, weeks_to_show=weeks_to_show)
        if not onsite_trend.empty:
            fig_onsites = go.Figure()
            for interviewer in ['Sam Nadler', 'Jordan Metzner']:
                interviewer_data = onsite_trend[onsite_trend['Interviewer'] == interviewer]
                fig_onsites.add_trace(go.Scatter(
                    x=interviewer_data['Week'],
                    y=interviewer_data['Total Onsites'],
                    name=interviewer,
                    mode='lines+markers'
                ))
            
            fig_onsites.update_layout(
                title='Weekly Onsite Interviews (Sam & Jordan)',
                height=400,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_onsites, use_container_width=True, key="sam_jordan_trend")

        # Detailed Metrics Table
        st.markdown("<h2 style='color: #0066cc;'>Detailed Metrics</h2>", unsafe_allow_html=True)
        
        try:
            # Get all metrics
            all_screen_metrics = get_recruiter_screen_metrics(df, weeks_to_show=weeks_to_show)
            all_onsite_metrics = get_onsite_conversion_metrics(df, weeks_to_show=weeks_to_show)
            
            # Merge metrics
            detailed_metrics = pd.merge(
                all_screen_metrics,
                all_onsite_metrics[['Week', 'Recruiter', 'Onsites', 'Conversion']],
                on=['Week', 'Recruiter'],
                how='left'
            )
            
            # Clean up and format
            detailed_metrics['Onsites'] = detailed_metrics['Onsites'].fillna(0).astype(int)
            detailed_metrics['Conversion'] = detailed_metrics['Conversion'].fillna(0).round(1)
            
            # Sort and display
            detailed_metrics_sorted = detailed_metrics.sort_values(
                ['Week', 'Recruiter'], 
                ascending=[False, True]
            )
            
            st.dataframe(
                detailed_metrics_sorted[[
                    'Week', 'Recruiter', 'Total Screens', 'Passes', 
                    'Pass Rate', 'Onsites', 'Conversion'
                ]],
                hide_index=True
            )
            
        except Exception as e:
            st.error(f"Error rendering detailed metrics: {str(e)}")

    except Exception as e:
        st.error(f"Error rendering dashboard: {str(e)}")

def main():
    """Main app function"""
    # Custom CSS for styling
    st.markdown("""
        <style>
        .stApp {
            background-color: #f8f9fa;
        }
        div[data-testid="stMetricValue"] {
            font-size: 24px;
            color: #0066cc;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 14px;
        }
        div[data-testid="metric-container"] {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin: 10px 0;
        }
        .chart-container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin: 10px 0;
        }
        .header-container {
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 10px;
            background: linear-gradient(90deg, #0066cc 0%, #0099ff 100%);
            color: white;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            margin: 1rem 0;
        }
        .file-record {
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            border-left: 3px solid #0066cc;
        }
        
        div.stSuccess {
            padding: 1rem;
            border-radius: 0.5rem;
        }
        
        h2 {
            padding: 0.5rem 0;
            border-bottom: 2px solid #0066cc;
            margin-bottom: 1.5rem;
        }
        
        div[data-testid="metric-container"] {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-top: 3px solid #0066cc;
        }
        
        .plot-container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin: 1rem 0;
        }
        
        div[data-testid="stDataFrame"] {
            background-color: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
        """, unsafe_allow_html=True)

    # Custom header
    st.markdown("""
        <div class="header-container">
            <h1 style='color: white;'>Ryz Labs Recruitment Analytics Dashboard</h1>
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        # Initialize session state
        if 'last_uploaded_file' not in st.session_state:
            st.session_state['last_uploaded_file'] = None
        
        # File uploader
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'], key='file_uploader')
        if uploaded_file is not None:
            handle_file_upload(uploaded_file)
    
    # Get current data
    df = get_current_data()
    
    # Render dashboard if we have data
    if not df.empty:
        render_metrics_dashboard(df)
    else:
        st.info("No data available. Please upload a CSV file.")

if __name__ == "__main__":
    main()
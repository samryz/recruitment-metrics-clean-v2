from setuptools import setup, find_packages

setup(
    name="recruitment-metrics",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'streamlit==1.31.0',
        'pandas==2.1.4',
        'plotly==5.18.0',
        'supabase==1.2.0',
        'python-dotenv==1.0.0',
        'python-dateutil>=2.8.2',
        'pytz>=2023.3',
    ],
    python_requires='>=3.9',
) 
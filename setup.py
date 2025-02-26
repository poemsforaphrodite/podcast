from setuptools import setup, find_packages

setup(
    name="podcast-trend-finder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
        "supabase>=2.0.0",
        "apify-client>=1.4.0",
        "openai>=1.3.0",
        "requests>=2.31.0",
        "python-logging>=0.4.9",
        "watchdog>=3.0.0",
    ],
) 
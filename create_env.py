#!/usr/bin/env python3
"""
Helper script to create the .env file with VIDEO_PATH configuration.
"""
import os


def create_env_file():
    """Create the .env file with VIDEO_PATH configuration."""
    env_content = '''VIDEO_PATH="/Volumes/Extreme_Pro/PS5/CREATE/Video Clips/Marvel Rivals/"
'''
    
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"⚠️  .env file already exists at {env_file}")
        print("Please edit it manually to set the correct VIDEO_PATH")
        return
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with VIDEO_PATH configuration")
        print(f"📁 File: {os.path.abspath(env_file)}")
        print("Please edit the VIDEO_PATH to match your actual video directory")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file() 
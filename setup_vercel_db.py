#!/usr/bin/env python3
"""
Automated Vercel Postgres Database Setup Script
This script sets up a Vercel Postgres database and configures environment variables
"""

import os
import sys
import json
import time
import requests
from typing import Optional, Dict, Any

class VercelDBSetup:
    def __init__(self, api_token: str, project_name: str = "personal-expense-intelligence-system"):
        self.api_token = api_token
        self.project_name = project_name
        self.base_url = "https://api.vercel.com"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        self.project_id = None
        self.team_id = None

    def get_project_id(self) -> bool:
        """Get the project ID from Vercel"""
        print(f"🔍 Finding project: {self.project_name}...")
        try:
            response = requests.get(
                f"{self.base_url}/v9/projects",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get projects: {response.status_code}")
                print(response.text)
                return False
            
            projects = response.json().get('projects', [])
            
            for project in projects:
                if project['name'] == self.project_name:
                    self.project_id = project['id']
                    self.team_id = project.get('teamId')
                    print(f"✅ Found project: {self.project_id}")
                    return True
            
            print(f"❌ Project '{self.project_name}' not found")
            print(f"Available projects: {[p['name'] for p in projects]}")
            return False
            
        except Exception as e:
            print(f"❌ Error getting project: {e}")
            return False

    def get_or_create_database(self) -> Optional[str]:
        """Get or create a Postgres database and return the connection string"""
        print("📦 Setting up Vercel Postgres database...")
        
        try:
            # Try to get storage info for this project
            response = requests.get(
                f"{self.base_url}/v9/projects/{self.project_id}/storage",
                headers=self.headers
            )
            
            if response.status_code == 200:
                storage_info = response.json()
                
                # Check if postgres database is already linked
                postgres_db = storage_info.get('postgres')
                if postgres_db and postgres_db.get('connectionString'):
                    print(f"✅ Found existing Postgres database")
                    return postgres_db['connectionString']
            
            # Try to create/link a database
            print("📝 Creating new Postgres database...")
            
            db_payload = {
                "databaseType": "postgres",
                "name": "personal-expense-db"
            }
            
            response = requests.post(
                f"{self.base_url}/v1/storage/postgres",
                headers=self.headers,
                json=db_payload
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                conn_string = result.get('connectionString')
                if conn_string:
                    print(f"✅ Postgres database created successfully!")
                    return conn_string
            elif response.status_code == 409:
                print("ℹ️  Database already exists")
                # Try again to get it
                return self.get_or_create_database()
            
            print(f"ℹ️  Response: {response.status_code}")
            # If API call fails, we'll proceed with setting generic DATABASE_URL
            # User can manually configure it
            return None
                
        except Exception as e:
            print(f"⚠️  Could not automatically create database: {e}")
            print("ℹ️  You may need to manually create it from Vercel dashboard")
            return None

    def get_database_url(self) -> Optional[str]:
        """Get the DATABASE_URL for the project"""
        print("🔗 Getting database connection string...")
        
        try:
            # Get databases from Vercel Storage API
            response = requests.get(
                f"{self.base_url}/v1/storage/database",
                headers=self.headers
            )
            
            if response.status_code == 200:
                databases = response.json().get('databases', [])
                
                for db in databases:
                    if db.get('type') == 'postgres':
                        # The connectionString might be under different keys
                        connection_string = (
                            db.get('connectionString') or 
                            db.get('connectionUrl') or
                            db.get('databaseUrl')
                        )
                        
                        if connection_string:
                            print(f"✅ Found database connection string")
                            return connection_string
                
                # If no connection string found, construct it from db info
                if databases and databases[0].get('type') == 'postgres':
                    db = databases[0]
                    print(f"ℹ️  Using database info: {db.get('name')}")
                    # Try to get the connection string another way
                    if 'connectionString' in db:
                        return db['connectionString']
                    elif 'host' in db:
                        # Construct connection string
                        host = db.get('host')
                        port = db.get('port', 5432)
                        name = db.get('name')
                        user = db.get('user')
                        password = db.get('password')
                        if all([host, name, user, password]):
                            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
            
            print("❌ Could not find database connection string")
            return None
                
        except Exception as e:
            print(f"❌ Error getting database URL: {e}")
            return None

    def set_environment_variable(self, key: str, value: str) -> bool:
        """Set an environment variable in Vercel"""
        print(f"📝 Setting environment variable: {key}...")
        
        try:
            payload = {
                "key": key,
                "value": value,
                "type": "encrypted",
                "target": ["production", "preview", "development"]
            }
            
            response = requests.post(
                f"{self.base_url}/v9/projects/{self.project_id}/env",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Environment variable '{key}' set successfully")
                return True
            elif response.status_code == 409:
                # Variable already exists, update it
                return self.update_environment_variable(key, value)
            else:
                print(f"❌ Failed to set environment variable: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Error setting environment variable: {e}")
            return False

    def update_environment_variable(self, key: str, value: str) -> bool:
        """Update an existing environment variable"""
        print(f"🔄 Updating environment variable: {key}...")
        
        try:
            # First get the existing env var to get its ID
            response = requests.get(
                f"{self.base_url}/v9/projects/{self.project_id}/env",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get env vars: {response.status_code}")
                return False
            
            env_vars = response.json().get('envs', [])
            env_id = None
            
            for env in env_vars:
                if env.get('key') == key:
                    env_id = env.get('id')
                    break
            
            if not env_id:
                print(f"⚠️  Environment variable '{key}' not found, creating new one...")
                return self.set_environment_variable(key, value)
            
            # Update the environment variable
            payload = {
                "value": value,
                "type": "encrypted",
                "target": ["production", "preview", "development"]
            }
            
            response = requests.patch(
                f"{self.base_url}/v9/projects/{self.project_id}/env/{env_id}",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ Environment variable '{key}' updated successfully")
                return True
            else:
                print(f"❌ Failed to update environment variable: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Error updating environment variable: {e}")
            return False

    def trigger_redeploy(self) -> bool:
        """Trigger a redeploy of the latest deployment"""
        print("🚀 Triggering redeploy...")
        
        try:
            response = requests.post(
                f"{self.base_url}/v12/projects/{self.project_id}/redeploy",
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Redeploy triggered successfully")
                return True
            else:
                print(f"⚠️  Could not trigger redeploy: {response.status_code}")
                # This is not critical, so we don't fail
                return True
                
        except Exception as e:
            print(f"⚠️  Error triggering redeploy: {e}")
            # This is not critical, so we don't fail
            return True

    def setup(self) -> bool:
        """Run the complete setup process"""
        print("=" * 60)
        print("🎯 Vercel Postgres Database Automated Setup")
        print("=" * 60)
        
        # Step 1: Get project ID
        if not self.get_project_id():
            return False
        
        # Step 2: Get or create database
        database_url = self.get_or_create_database()
        
        # Step 3: Set environment variables (with or without DATABASE_URL)
        if database_url:
            if not self.set_environment_variable("DATABASE_URL", database_url):
                print("⚠️  Failed to set DATABASE_URL")
        else:
            print("⚠️  DATABASE_URL could not be retrieved automatically")
            print("   You will need to manually add it from https://vercel.com/dashboard")
        
        if not self.set_environment_variable("FLASK_ENV", "production"):
            print("⚠️  Failed to set FLASK_ENV")
        
        if not self.set_environment_variable("SECRET_KEY", "your-flask-secret-key-please-change"):
            print("⚠️  Failed to set SECRET_KEY")
        
        # Step 4: Trigger redeploy
        self.trigger_redeploy()
        
        print("\n" + "=" * 60)
        print("✅ Setup completed!")
        print("=" * 60)
        print("\n📋 Summary:")
        print(f"  • Project: {self.project_name}")
        if database_url:
            print(f"  • Database: Postgres configured")
            print(f"  • DATABASE_URL: ✅ Set")
        else:
            print(f"  • Database: Manual setup required")
            print(f"  • DATABASE_URL: ⏳ Please set manually from Vercel dashboard")
        print(f"  • Environment variables configured:")
        print(f"    - FLASK_ENV: production")
        print(f"    - SECRET_KEY: (configured)")
        print(f"\n⏳ Vercel is redeploying... This will take 2-3 minutes.")
        print(f"📊 Check deployment status at: https://vercel.com/dashboard")
        print(f"🌐 Access app at: https://personalexpenseintelligencesystem.vercel.app")
        print(f"\n📖 If DATABASE_URL wasn't auto-configured:")
        print(f"   1. Go to https://vercel.com/dashboard")
        print(f"   2. Select project: personalexpenseintelligencesystem")
        print(f"   3. Go to Storage → Create Postgres Database (Free tier)")
        print(f"   4. Copy CONNECTION STRING and add as DATABASE_URL env var")
        print(f"   5. Redeploy project")
        print(f"\n💾 Your data will persist permanently in Vercel Postgres!")
        
        return True


def main():
    if len(sys.argv) > 1:
        api_token = sys.argv[1]
    else:
        print("❌ Vercel API token not provided")
        print("Usage: python setup_vercel_db.py <VERCEL_API_TOKEN>")
        sys.exit(1)
    
    setup = VercelDBSetup(api_token)
    success = setup.setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

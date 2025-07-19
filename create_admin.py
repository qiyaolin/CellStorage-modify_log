#!/usr/bin/env python3
"""Script to create an admin user in the database."""

from app import create_app, db
from app.models import User

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("Admin user already exists!")
            return
        
        # Create new admin user
        admin = User(username='admin', role='admin')
        admin.set_password('111111')
        
        db.session.add(admin)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: 111111")
        print("Role: admin")

if __name__ == '__main__':
    create_admin_user()
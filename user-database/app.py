"""
User Database API - Manages up to 100 users and logs requests
"""
import os
import json
import random
from datetime import datetime
from flask import Flask, jsonify
from faker import Faker

app = Flask(__name__)
fake = Faker()

# Configuration
DATA_DIR = '/data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
LOGS_FILE = os.path.join(DATA_DIR, 'user_database.log')
MAX_USERS = 100

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)


def load_users():
    """Load users from JSON file."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_users(users):
    """Save users to JSON file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def log_request(user_id, user_name, action):
    """Log request in JSON format."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "user-database",
        "action": action,
        "user_id": user_id,
        "user_name": user_name
    }
    
    # Write to log file
    with open(LOGS_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    return log_entry


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/user/random', methods=['GET'])
def get_random_user():
    """Get a random user - either existing or create new (up to 100)."""
    users = load_users()
    
    # If we have users, 70% chance to return existing, 30% to create new
    if users and (len(users) >= MAX_USERS or random.random() < 0.7):
        # Return existing user
        user = random.choice(users)
        log_request(user['id'], user['name'], 'returned_existing')
        return jsonify(user), 200
    
    # Create new user if under limit
    if len(users) < MAX_USERS:
        new_user = {
            "id": len(users) + 1,
            "name": fake.name()
        }
        users.append(new_user)
        save_users(users)
        log_request(new_user['id'], new_user['name'], 'created_new')
        return jsonify(new_user), 201
    
    # If at max, return random existing user
    user = random.choice(users)
    log_request(user['id'], user['name'], 'returned_existing_max_reached')
    return jsonify(user), 200


@app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users."""
    users = load_users()
    return jsonify({
        "count": len(users),
        "max": MAX_USERS,
        "users": users
    }), 200


@app.route('/users/reset', methods=['POST'])
def reset_users():
    """Reset all users (for testing)."""
    save_users([])
    return jsonify({"message": "Users reset successfully"}), 200


if __name__ == '__main__':
    print("User Database API starting...", flush=True)
    app.run(host='0.0.0.0', port=8500, debug=False)

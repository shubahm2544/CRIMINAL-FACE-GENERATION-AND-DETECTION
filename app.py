from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify, Response
import os
import mysql.connector
from mysql.connector import Error
import torch
import cv2
import numpy as np
import clip
import face_recognition
from PIL import Image
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime, timedelta
import logging
import time
import base64
import re

// SOME OF THE CODE IS HIDDEN HERE // 
    verify_dataset()
except Exception as e:
    print(f"Dataset verification failed: {str(e)}")

@app.route('/test_camera')
def test_camera():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return jsonify({"error": "Failed to open camera"}), 500
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({"error": "Failed to read from camera"}), 500
            
        return jsonify({"success": "Camera is working"}), 200
    except Exception as e:
        return jsonify({"error": f"Camera error: {str(e)}"}), 500

@app.route('/setup_db')
def setup_db():
    try:
        db = get_db_connection()
        if not db:
            return "Failed to connect to database"
        
        cursor = db.cursor()
        
        # Create users table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create criminals table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS criminals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                age INT NOT NULL,
                gender VARCHAR(50) NOT NULL,
                crime TEXT NOT NULL,
                image_path VARCHAR(255) NOT NULL,
                facial_embedding MEDIUMBLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create a test user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create a default user (username: admin, password: admin123)
            hashed_password = generate_password_hash('admin123')
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                ('admin', hashed_password)
            )
        
        db.commit()
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Get criminal count
        cursor.execute("SELECT COUNT(*) FROM criminals")
        criminal_count = cursor.fetchone()[0]
        
        cursor.close()
        db.close()
        
        return jsonify({
            "status": "success",
            "tables": [table[0] for table in tables],
            "user_count": user_count,
            "criminal_count": criminal_count,
            "message": "Database setup complete"
        })
        
    except Error as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

// SOME OF THE CODE IS HIDDEN //
@app.route('/reset_admin')
def reset_admin():
    try:
        db = get_db_connection()
        if not db:
            return jsonify({"error": "Database connection failed"})
        
        cursor = db.cursor()
        try:
            # Delete existing admin user
            cursor.execute("DELETE FROM users WHERE username = 'admin'")
            
            # Create new admin user
            password = 'admin123'
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                ('admin', hashed_password)
            )
            
            db.commit()
            
            # Verify the user was created
            cursor.execute("SELECT username, password FROM users WHERE username = 'admin'")
            user = cursor.fetchone()
            
            return jsonify({
                "status": "success",
                "message": "Admin user reset successfully",
                "credentials": {
                    "username": "admin",
                    "password": "admin123"
                },
                "verification": {
                    "user_exists": user is not None,
                    "password_hash": user[1] if user else None
                }
            })
            
        finally:
            cursor.close()
            db.close()
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/video_progress')
def video_progress():
    def generate():
        while True:
            # Get progress from a global variable or cache
            progress = 0  # You'll need to implement progress tracking
            yield f"data: {json.dumps({'progress': progress})}\n\n"
            if progress >= 100:
                break
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

//  SOME OF THE CODE HERE IS HIDDEN //

@app.route('/test_password/<username>/<password>')
def test_password(username, password):
    try:
        db = get_db_connection()
        if not db:
            return jsonify({"error": "Database connection failed"})
        
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            })
            
        password_check = check_password_hash(user['password'], password)
        
        return jsonify({
            "status": "success",
            "username": username,
            "stored_hash": user['password'],
            "password_check": password_check
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })
    finally:
        cursor.close()
        db.close()

# This should be at the end of the file
if __name__ == '__main__':
    create_default_alert_sound()
    app.run(debug=True)

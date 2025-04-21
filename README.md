# Cyberbullying Detection System

A web application that detects cyberbullying in text using machine learning.

## Features
- Text analysis for cyberbullying detection
- User login system
- Report submission system
- Responsive web interface

## Setup Instructions

1. Install Python 3.7 or higher
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python app.py
   ```
4. Open your browser and navigate to `http://localhost:5000`

## Project Structure
- `app.py`: Main Flask application
- `templates/`: HTML templates
  - `index.html`: Home page
  - `login.html`: Login page
  - `report.html`: Report submission page
- `static/`: Static files (CSS, JS)
- `LinearSVC.pkl`: Trained model
- `tfidfvectoizer.pkl`: TF-IDF vectorizer
- `stopwords.txt`: Stop words for text processing 
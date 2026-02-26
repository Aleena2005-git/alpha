import requests
import os
from transformers import pipeline
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, request, render_template, jsonify

load_dotenv()

sentiment_analyzer = pipeline('sentiment-analysis')

solutions = {
    "defective": "We're sorry to hear that the product was defective. Please reach out to our customer service team for a replacement or refund.",
    "damaged": "We apologize for the damage to the product. Kindly contact our customer service to resolve this issue.",
    "disappointed": "We apologize for your dissatisfaction. We're working hard to improve our products. Please let us know how we can make this right."
}


# Get MongoDB URI from environment variables
MONGO_URI = os.environ.get("MONGO_URI")

# Connect to MongoDB using PyMongo
try:
    client = MongoClient(MONGO_URI)
    # If you have a specific database name, you can use:
    # db = client["your_database_name"]
    db = client['sentiment_analysis']  # This works if the default DB is set in the URI
    reviews_collection = db["reviews"]  # This is equivalent to the Review model collection in Mongoose
    print("Connected to MongoDB")
except Exception as e:
    print("MongoDB Connection Error:", e)
    raise e

# Function to analyze sentiment and generate a solution
def generate_solution(negative_review):
    # Get the sentiment of the review
    sentiment = sentiment_analyzer(negative_review)

    if sentiment[0]['label'] == 'NEGATIVE':
        # Check for specific keywords in the review and return a corresponding solution
        for keyword, solution in solutions.items():
            if keyword in negative_review.lower():
                return solution
        # Default solution if no specific keyword found
        return "We're sorry for the inconvenience. Please contact support for further assistance."
    else:
        return "Thank you for your positive feedback!"


def submit_problem_solution(problem, solution):
    data = {
        'problem': problem,
        'solution': solution
    }
    try:
        reviews_collection.insert_one(data)
    except Exception as e:
        print("Error saving problem-solution pair:", e)


# Initialize the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/admin')
def admin_page():
    return render_template("admin.html")

@app.route('/submit', methods=['POST'])
def submit_review():
    review = request.form['review']
    sentiment = sentiment_analyzer(review)
    
    # Indentation for the if statement
    if sentiment[0]['label'] == 'NEGATIVE':
        solution = generate_solution(review)
        submit_problem_solution(review, solution)
        return render_template('solution.html', solution=solution)
    else:
        return render_template('solution.html', solution="No issues found with your review.")

# GET endpoint to fetch all reviews from MongoDB
@app.route("/getReviews", methods=["GET"])
def get_reviews():
    try:
        # Retrieve all documents from the "reviews" collection
        reviews = list(reviews_collection.find())
        # Convert each document's ObjectId to a string for JSON serialization
        for review in reviews:
            review["_id"] = str(review["_id"])
        return jsonify(reviews), 200
    except Exception as e:
        print("Error fetching reviews:", e)
        return jsonify({"message": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
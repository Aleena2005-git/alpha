import requests
from transformers import pipeline
sentiment_analyzer = pipeline('sentiment-analysis')

review = "The product is bad, and I am very disappointed with the quality."
from transformers import pipeline
reviews = [
    "This product is amazing! I'm very happy with it.",
    "Terrible product. It broke after one use.",
    "It's okay, but not worth the price.",
    "I love this! Highly recommend it.",
    "Worst purchase ever. Very disappointed."
]
print("Negative Reviews:")
solutions = {
    "defective": "We're sorry to hear that the product was defective. Please reach out to our customer service team for a replacement or refund.",
    "damaged": "We apologize for the damage to the product. Kindly contact our customer service to resolve this issue.",
    "disappointed": "We apologize for your dissatisfaction. We're working hard to improve our products. Please let us know how we can make this right."
}

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
    # URL of your API endpoint
    api_url = 'http://localhost:3000/review'  # Adjust this to your actual API URL

    # Create a dictionary to send as JSON
    data = {
        'problem': problem,
        'solution': solution
    }

    try:
        # Make a POST request to the server
        response = requests.post(api_url, json=data)

        # Check the response status code
        if response.status_code == 201:
            print("Problem and solution successfully submitted!")
            print("Response Data:", response.json())
        else:
            print(f"Failed to submit. Status code: {response.status_code}")
            print("Response:", response.text)
        return

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return

# Example usage
# problem = "How to handle exceptions in Python?"
# solution = "Use try-except blocks to catch and handle exceptions."

def generate_solution(review):
    if "hole" in review or "damaged" in review:
        return "We're sorry about the issue with your product. Please reach out to our customer support team for a replacement."
    elif "size" in review or "fit" in review:
        return "We apologize for the size issue. You can return or exchange the product through our website."
    else:
        return "We apologize for the inconvenience. Please contact support for assistance."

from flask import Flask, request, render_template

# Initialize the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

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

# Ensure that this line has the correct indentation
if __name__ == "__main__":
    app.run(debug=True)
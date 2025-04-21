from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

# Dummy report storage
reported_messages = []

@app.route("/", methods=["GET", "POST"])
def home():
    prediction = None
    input_text = ""

    if request.method == "POST":
        input_text = request.form["text"]
        if "bully" in input_text.lower():
            prediction = -1  # Example: Detecting "bully" as bullying
        else:
            prediction = 1  # Non-bullying

    return render_template("index.html", prediction=prediction, input_text=input_text)

@app.route("/report", methods=["POST"])
def report():
    message = request.form["message"]
    reported_messages.append(message)
    return redirect("/reports")

@app.route("/reports")
def reports():
    return render_template("reports.html", reports=reported_messages)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        return redirect("/")
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)

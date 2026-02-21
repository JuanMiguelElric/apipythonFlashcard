from flask import Flask
from Controller.FlashcardController import FlashcardController

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "hellow world"

@app.route("/submit_flash",methods=['POST'])
def submit_flash():
    return FlashcardController.create_post()
if __name__ == "__main__":
    app.run(debug=True)
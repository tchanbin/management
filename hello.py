# hello.py
from flask import Flask
from flask_script import Manager
app=Flask(__name__)
manager=Manager(app)

@app.route('/',methods=['GET'])
def index():
    return "Hello Flask!      eagewtew "

if __name__=='__main__':
    manager.run(debug=True)
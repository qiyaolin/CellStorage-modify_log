# serve.py
from waitress import serve
from run import application

if __name__ == '__main__':
    serve(application, host='10.67.1.10', port=5000)
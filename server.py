import requests
import os
from flask import Flask, request, send_file, flash, redirect, render_template, url_for, jsonify
from werkzeug.utils import secure_filename
import PIL
from PIL import Image, ImageOps
import base64
import cv2
import numpy as np
import tempfile
import io
from queue import Queue, Empty
import time
import threading
import constant



UPLOAD_FOLDER = '/static'

app = Flask(__name__, template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024*5
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

requests_queue = Queue()
BATCH_SIZE = 1
CHECK_INTERVAL = 0.1

easy_ocr_addr = constant.ocr_url
tts_addr = constant.tts_url


def handle_requests_by_batch():
    while True:
        requests_batch = []
        while not (len(requests_batch) >= BATCH_SIZE):
            try:
                requests_batch.append(requests_queue.get(timeout=CHECK_INTERVAL))
            except Empty:
                continue
            batch_outputs = []
            for request in requests_batch:
                batch_outputs.append(run(request['input'][0]))

            for request, output in zip(requests_batch, batch_outputs):
                request['output'] = output


threading.Thread(target=handle_requests_by_batch).start()


def run(input_image):

    # print(filename)
    files_for_ocr = [
        ('base_image', input_image)
    ]
    ocr_data = {'language':'af'}
    headers ={}

    ocr_response = requests.request("POST", easy_ocr_addr, headers=headers, data=ocr_data, files=files_for_ocr)
    print(ocr_response.status_code)
    if ocr_response.status_code == 429:
        return 429
    elif ocr_response.status_code == 500:
        return 'OCR Server Error'

    extracted_text = str(ocr_response.text)
    print("ocr done")
    print(extracted_text)

    tts_data = {'input_text': extracted_text,
    'batched': 'True'}
    headers= {}
    for _ in range(5):
        tts_response = requests.request("POST", tts_addr, headers=headers, data = tts_data)
        if tts_response.status_code == 200:
            break
        elif tts_response.status_code == 429:
            time.sleep(1)
        else:
            break
    
    print("tts done")
    print(tts_response.status_code)
    
    if tts_response.status_code == 429:
        return 429 
    elif tts_response.status_code == 500:
        return 'TTS Server Error'

    return tts_response.content


@app.route('/', methods=['GET', 'POST'])
def index():
    print("index")
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        print("start")
        if 'file' not in request.files:
            print('no file')
            return jsonify({'msg':'Please input image'}),400
        input_image = request.files['file']
        
        try:
            PIL.Image.open(input_image).convert("RGB")
        except Exception: 
            return jsonify({'msg':'Please input image'}), 400

        if input_image.filename == '':
            print('no filename')
            return jsonify({'msg':'No filename'}), 400
        input_image = PIL.Image.open(input_image)
        buf = io.BytesIO()
        input_image.save(buf, format='PNG')
        byte_file = buf.getvalue()
        
        if requests_queue.qsize() >= BATCH_SIZE:
            return jsonify({'msg':'Too Many Requests. Please try again'}), 429

        req = {
            'input': [byte_file]
        }
        requests_queue.put(req)

        while 'output' not in req:
            time.sleep(CHECK_INTERVAL)

        if req['output'] == 429:
            return jsonify({'msg':'Too Many Requests. Please try again'}), 429
        elif 'error' in req['output'] : 
            return jsonify({'msg':req['output']}), 500
            
        byte_io = io.BytesIO(req['output'])
        byte_io.seek(0)
        return send_file(byte_io, mimetype="audio/wav")
    return render_template('index.html')


@app.route('/healthz', methods=['GET'])
def checkHealth():
	return "Pong",200


@app.errorhandler(413)
def request_entity_too_large(error):
    # return {'error': 'File Too Large'}, 413
    # return render_template('index.html', result = 'The image size is too large'), 413
    return jsonify({'msg':'The image size is too large'}),413


if __name__ == '__main__':
    app.run(debug=False, port=8000, host='0.0.0.0', threaded=True)

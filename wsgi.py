import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, send_from_directory, jsonify
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = 'uploads'
Bootstrap(application)

if not os.path.exists(application.config['UPLOAD_FOLDER']):
    os.makedirs(application.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'eaf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def phonetic_to_orthography(phonetic):
    # Define the mapping rules from phonetic to orthography for digraphs and single phonemes
    mapping = {
        'tʃ': 'x',
        "ã": "ã",
        "õ": "õ",
        "ẽ": "ẽ",
        "ĩ": "ĩ",
        "ũ": "ũ",
        'õã': 'oã',
        'õĩ': 'oĩ',
        'ũã': 'uã',
        'ᵐb': 'mb',
        'ᵑg': 'ng',
        'ⁿd': 'nd',
        'β': 'w',
        "'": "",
        "ʼ": "",
        '.': '',
        'õn': 'on',
        'ũn': 'on',
        'ĩn': 'in',
        'ɛ̃n': 'en',
        'ẽn': 'en',
        'ãn': 'an',
        'õɲ': 'oɲ',
        'ũɲ': 'oɲ',
        'ĩɲ': 'iɲ',
        'ɛ̃ɲ': 'eɲ',
        'ẽɲ': 'eɲ',
        'ãɲ': 'aɲ',
        'õm': 'om',
        'ũm': 'om',
        'ĩm': 'im',
        'ẽm': 'em',
        'ãm': 'am',
        'u': 'o',
        'ɨ̃n': 'un',
        'ɨ̃ɲ': 'uɲ',
        'ɨ̃m': 'um',
        'ɨ': 'u',
        'e:': 'ee',
        'ɛ:': 'ee',
        'o:': 'oo',
        'i:': 'ii',
        'ɲ': 'y',
        'j': 'y',
        'ʒ': 'y',
        'p̚': 'p',
        't̚': 't',
        'k̚': 'k',
        'pi.ãn': 'pian',
        'ɾ': 'r',
        'a': 'a',
        'ɛ': 'e',
        'o': 'o',
        'r': 'r',
        'p': 'p',
        't': 't',
        'm': 'm',
        'n': 'n',
        'k': 'k',
        'w': 'w',
        'i': 'i',
        'β': 'w',
        'ɾ': 'r',
    }

    orthographic = phonetic
    # Apply the mapping rules
    for key in mapping:
        orthographic = orthographic.replace(key, mapping[key])

    return orthographic

@application.route('/', methods=['GET'])
def upload():
    return render_template('upload.html')

@application.route('/transform', methods=['POST'])
def transform():
    data = request.json
    phonetic_text = data.get('phonetic_text', '')
    orthographic_text = phonetic_to_orthography(phonetic_text)
    return jsonify({'orthographic_text': orthographic_text})

@application.route('/results', methods=['POST'])
def results():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return render_template('upload.html', error='No selected file')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        try:
            # Example transformation (adjust as needed)
            transformed_file_path = transform_eaf(file_path)
            transformed_filename = os.path.basename(transformed_file_path)
            
            return render_template('results.html', 
                                   download_filename=transformed_filename)
        except ET.ParseError:
            error = "The uploaded file is not a valid .eaf XML file."
            return render_template('upload.html', error=error)

    return render_template('upload.html', error='Invalid file extension')

@application.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(application.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    application.run(debug=True)

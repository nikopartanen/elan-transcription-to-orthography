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
    for key in mapping:
        orthographic = orthographic.replace(key, mapping[key])

    return orthographic

def orthography_to_phonetic(orthography):
    mapping = {
        'x': 'tʃ',
        "ã": "ã",
        "õ": "õ",
        "ẽ": "ẽ",
        "ĩ": "ĩ",
        "ũ": "ũ",
        'oã': 'õã',
        'oĩ': 'õĩ',
        'uã': 'ũã',
        'mb': 'ᵐb',
        'ng': 'ᵑg',
        'nd': 'ⁿd',
        'w': 'β',
        'on': 'õn',
        'in': 'ĩn',
        'en': 'ẽn',
        'an': 'ãn',
        'oɲ': 'õɲ',
        'iɲ': 'ĩɲ',
        'eɲ': 'ẽɲ',
        'aɲ': 'ãɲ',
        'om': 'õm',
        'im': 'ĩm',
        'em': 'ẽm',
        'am': 'ãm',
        'o': 'u',
        'un': 'ɨ̃n',
        'uɲ': 'ɨ̃ɲ',
        'um': 'ɨ̃m',
        'u': 'ɨ',
        'ee': 'e:',
        'oo': 'o:',
        'ii': 'i:',
        'y': 'ɲ',
        'pian': 'pi.ãn',
        'r': 'ɾ',
        'a': 'a',
        'e': 'ɛ',
        'o': 'o',
        'p': 'p',
        't': 't',
        'm': 'm',
        'n': 'n',
        'k': 'k',
        'w': 'w',
        'i': 'i',
    }

    phonetic = orthography
    for key in mapping:
        phonetic = phonetic.replace(key, mapping[key])

    return phonetic

def transform_annotations_for_all_participants(source_file):
    tree = ET.parse(source_file)
    root = tree.getroot()
    transformed_annotations = []

    for tier in root.findall('TIER'):
        if 'PARTICIPANT' in tier.attrib and tier.attrib['LINGUISTIC_TYPE_REF'] == 'Transcription':
            participant = tier.attrib['PARTICIPANT']
            source_tier_id = tier.attrib['TIER_ID']
            target_tier_id = f"{participant}_Ortography-gls-mpu"

            target_tier = None
            for existing_tier in root.findall('TIER'):
                if existing_tier.get('TIER_ID') == target_tier_id:
                    target_tier = existing_tier
                    break

            if target_tier is None:
                target_tier = ET.SubElement(root, 'TIER', {
                    'LINGUISTIC_TYPE_REF': 'Ortografia',
                    'PARENT_REF': source_tier_id,
                    'PARTICIPANT': participant,
                    'TIER_ID': target_tier_id
                })
                ET.SubElement(target_tier, 'ANNOTATION')

            for annotation in tier.findall('ANNOTATION/ALIGNABLE_ANNOTATION'):
                annotation_id = annotation.get('ANNOTATION_ID')
                annotation_value_element = annotation.find('ANNOTATION_VALUE')
                annotation_text = annotation_value_element.text if annotation_value_element is not None else ""

                if annotation_text.strip():
                    transformed_text = phonetic_to_orthography(annotation_text)
                    transformed_annotations.append((annotation_text, transformed_text))

                    new_annotation = ET.Element('ALIGNABLE_ANNOTATION', {
                        'ANNOTATION_ID': annotation_id,
                        'TIME_SLOT_REF1': annotation.get('TIME_SLOT_REF1'),
                        'TIME_SLOT_REF2': annotation.get('TIME_SLOT_REF2')
                    })
                    new_annotation_value = ET.SubElement(new_annotation, 'ANNOTATION_VALUE')
                    new_annotation_value.text = transformed_text

                    target_tier.find('ANNOTATION').append(new_annotation)

    return ET.ElementTree(root), transformed_annotations

def transform_eaf(file_path):
    transformed_path = os.path.join(application.config['UPLOAD_FOLDER'], 'orthography_' + os.path.basename(file_path))

    tree, transformed_annotations = transform_annotations_for_all_participants(file_path)
    tree.write(transformed_path, encoding='UTF-8', xml_declaration=True)

    return transformed_path, transformed_annotations

@application.route('/', methods=['GET'])
def upload():
    return render_template('upload.html')

@application.route('/transform_ipa', methods=['POST'])
def transform_ipa():
    data = request.json
    phonetic_text = data.get('phonetic_text', '')
    orthographic_text = phonetic_to_orthography(phonetic_text)
    return jsonify({'orthographic_text': orthographic_text})

@application.route('/transform_orthography', methods=['POST'])
def transform_orthography():
    data = request.json
    orthographic_text = data.get('orthographic_text', '')
    phonetic_text = orthography_to_phonetic(orthographic_text)
    return jsonify({'phonetic_text': phonetic_text})

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
            transformed_file_path, transformed_annotations = transform_eaf(file_path)
            transformed_filename = os.path.basename(transformed_file_path)
            
            return render_template('results.html', 
                                   download_filename=transformed_filename,
                                   annotations=transformed_annotations)
        except ET.ParseError:
            error = "The uploaded file is not a valid .eaf XML file."
            return render_template('upload.html', error=error)

    return render_template('upload.html', error='Invalid file extension')

@application.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(application.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    application.run(debug=True)

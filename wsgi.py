import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pympi

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

import xml.etree.ElementTree as ET

def transform_annotations_for_all_participants(source_file, target_file):
    # Parse the EAF file
    tree = ET.parse(source_file)
    root = tree.getroot()

    # Iterate over all TIER elements
    for tier in root.findall('TIER'):
        # Check if the tier has the expected attributes
        if 'PARTICIPANT' in tier.attrib and tier.attrib['LINGUISTIC_TYPE_REF'] == 'Transcription':
            participant = tier.attrib['PARTICIPANT']
            source_tier_id = tier.attrib['TIER_ID']
            target_tier_id = f"{participant}_Ortography-gls-mpu"
            
            # Find or create the target tier
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

            # Iterate over annotations in the source tier
            for annotation in tier.findall('ANNOTATION/ALIGNABLE_ANNOTATION'):
                annotation_id = annotation.get('ANNOTATION_ID')
                annotation_value_element = annotation.find('ANNOTATION_VALUE')
                annotation_text = annotation_value_element.text if annotation_value_element is not None else ""

                # Check if the annotation is empty
                if not annotation_text.strip():
                    # Transform the annotation text
                    transformed_text = phonetic_to_orthography(annotation_text)

                    # Create a new annotation in the target tier
                    new_annotation = ET.Element('ALIGNABLE_ANNOTATION', {
                        'ANNOTATION_ID': annotation_id,
                        'TIME_SLOT_REF1': annotation.get('TIME_SLOT_REF1'),
                        'TIME_SLOT_REF2': annotation.get('TIME_SLOT_REF2')
                    })
                    new_annotation_value = ET.SubElement(new_annotation, 'ANNOTATION_VALUE')
                    new_annotation_value.text = transformed_text

                    target_tier.find('ANNOTATION').append(new_annotation)

    # Write the modified XML back to a file
    tree.write(target_file, encoding='UTF-8', xml_declaration=True)

def transform_eaf(file_path):
    
    transformed_path = os.path.join(application.config['UPLOAD_FOLDER'], 'orthography_' + os.path.basename(file_path))

    transform_annotations_for_all_participants(file_path, transformed_path)

    return transformed_path

@application.route('/', methods=['GET'])
def upload():
    return render_template('upload.html')

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

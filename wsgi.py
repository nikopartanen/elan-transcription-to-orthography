import os
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, send_from_directory, jsonify, Response
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import csv
import io

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
        "ã": "ã",
        "õ": "õ",
        "ẽ": "ẽ",
        "ĩ": "ĩ",
        "ũ": "ũ",
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

def extract_annotations_with_metadata(source_file):
    tree = ET.parse(source_file)
    root = tree.getroot()
    
    # Extract time slots for reference
    time_slots = {}
    for time_slot in root.findall('.//TIME_ORDER/TIME_SLOT'):
        time_slots[time_slot.get('TIME_SLOT_ID')] = time_slot.get('TIME_VALUE')
    
    annotation_data = []
    
    for tier in root.findall('TIER'):
        if 'PARTICIPANT' in tier.attrib and tier.attrib['LINGUISTIC_TYPE_REF'] == 'Transcription':
            participant = tier.attrib['PARTICIPANT']
            tier_id = tier.attrib['TIER_ID']
            
            for annotation in tier.findall('.//ALIGNABLE_ANNOTATION'):
                annotation_id = annotation.get('ANNOTATION_ID')
                time_slot_ref1 = annotation.get('TIME_SLOT_REF1')
                time_slot_ref2 = annotation.get('TIME_SLOT_REF2')
                
                # Convert time values to seconds for display
                start_time_ms = int(time_slots.get(time_slot_ref1, 0))
                end_time_ms = int(time_slots.get(time_slot_ref2, 0))
                start_time_sec = start_time_ms / 1000.0
                end_time_sec = end_time_ms / 1000.0
                
                annotation_value_element = annotation.find('ANNOTATION_VALUE')
                if annotation_value_element is not None:
                    annotation_text = annotation_value_element.text if annotation_value_element.text is not None else ""
                    
                    if annotation_text.strip():
                        transformed_text = phonetic_to_orthography(annotation_text)
                        
                        annotation_data.append({
                            'annotation_id': annotation_id,
                            'participant': participant,
                            'tier_id': tier_id,
                            'start_time': f"{start_time_sec:.3f}",
                            'end_time': f"{end_time_sec:.3f}",
                            'phonetic': annotation_text,
                            'orthographic': transformed_text,
                            'time_slot_ref1': time_slot_ref1,
                            'time_slot_ref2': time_slot_ref2
                        })
    
    return annotation_data

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
                annotation_element = ET.SubElement(target_tier, 'ANNOTATION')

            for annotation in tier.findall('.//ALIGNABLE_ANNOTATION'):
                annotation_id = annotation.get('ANNOTATION_ID')
                annotation_value_element = annotation.find('ANNOTATION_VALUE')
                
                if annotation_value_element is not None:
                    annotation_text = annotation_value_element.text if annotation_value_element.text is not None else ""

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

                        # Find the annotation element to append to
                        for ann_elem in target_tier.findall('ANNOTATION'):
                            ann_elem.append(new_annotation)
                            break

    return ET.ElementTree(root), transformed_annotations

def generate_eaf_with_transformed_tiers(annotation_data, original_file_path):
    """
    Generate a new EAF file with the transformed annotations
    """
    # Start by parsing the original file to maintain structure
    tree = ET.parse(original_file_path)
    root = tree.getroot()
    
    # Group annotations by participant
    participants = {}
    for item in annotation_data:
        participant = item['participant']
        if participant not in participants:
            participants[participant] = []
        participants[participant].append(item)
    
    # Create orthography tiers for each participant
    for participant, annotations in participants.items():
        if not annotations:
            continue
            
        # Get source tier ID from the first annotation
        source_tier_id = annotations[0]['tier_id']
        target_tier_id = f"{participant}_Ortography-gls-mpu"
        
        # Check if the target tier already exists and remove it if it does
        for tier in root.findall('TIER'):
            if tier.get('TIER_ID') == target_tier_id:
                root.remove(tier)
        
        # Create new target tier
        target_tier = ET.SubElement(root, 'TIER', {
            'LINGUISTIC_TYPE_REF': 'Ortografia',
            'PARENT_REF': source_tier_id,
            'PARTICIPANT': participant,
            'TIER_ID': target_tier_id
        })
        
        annotation_container = ET.SubElement(target_tier, 'ANNOTATION')
        
        # Add annotations to the tier
        for item in annotations:
            new_annotation = ET.SubElement(annotation_container, 'ALIGNABLE_ANNOTATION', {
                'ANNOTATION_ID': item['annotation_id'],
                'TIME_SLOT_REF1': item['time_slot_ref1'],
                'TIME_SLOT_REF2': item['time_slot_ref2']
            })
            
            annotation_value = ET.SubElement(new_annotation, 'ANNOTATION_VALUE')
            annotation_value.text = item['orthographic']
    
    # Generate transformed file path
    transformed_path = os.path.join(application.config['UPLOAD_FOLDER'], 'orthography_' + os.path.basename(original_file_path))
    
    # Write the tree to the file
    tree.write(transformed_path, encoding='UTF-8', xml_declaration=True)
    
    return transformed_path

def generate_csv_export(annotation_data):
    """
    Generate a CSV file with the annotation data
    """
    output = io.StringIO()
    fieldnames = ['participant', 'tier_id', 'start_time', 'end_time', 'phonetic', 'orthographic']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for item in annotation_data:
        writer.writerow({
            'participant': item['participant'],
            'tier_id': item['tier_id'],
            'start_time': item['start_time'],
            'end_time': item['end_time'],
            'phonetic': item['phonetic'],
            'orthographic': item['orthographic']
        })
    
    return output.getvalue()

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
        return render_template('upload.html', error='No file part')

    file = request.files['file']
    if file.filename == '':
        return render_template('upload.html', error='No selected file')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        validity_checks = []

        # Perform validity checks
        if not check_file_is_well_formed(file_path):
            validity_checks.append("The file is not well-formed XML.")
        if not check_tier_structure(file_path):
            validity_checks.append("The tier structure is incorrect or missing expected tiers.")
        if not check_annotations_have_values(file_path):
            validity_checks.append("Some annotations do not have ANNOTATION_VALUE elements.")
        # Add more checks as needed

        if validity_checks:
            return render_template('upload.html', error=' '.join(validity_checks))

        try:
            # Extract annotation data with metadata
            annotation_data = extract_annotations_with_metadata(file_path)
            
            # Generate EAF file with transformed annotations for download
            transformed_file_path = generate_eaf_with_transformed_tiers(annotation_data, file_path)
            transformed_filename = os.path.basename(transformed_file_path)
            
            return render_template('results.html', 
                                   download_filename=transformed_filename,
                                   annotations=annotation_data,
                                   original_filename=filename,
                                   validity_checks=validity_checks)
        except ET.ParseError:
            error = "The uploaded file is not a valid .eaf XML file."
            return render_template('upload.html', error=error)

    return render_template('upload.html', error='Invalid file extension')

@application.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(application.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@application.route('/download_csv/<filename>')
def download_csv(filename):
    file_path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
    try:
        annotation_data = extract_annotations_with_metadata(file_path)
        csv_data = generate_csv_export(annotation_data)
        
        # Generate a filename for the CSV
        csv_filename = filename.rsplit('.', 1)[0] + '_annotations.csv'
        
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={csv_filename}"}
        )
    except Exception as e:
        return str(e), 500

# Example functions to check file validity
def check_file_is_well_formed(file_path):
    try:
        ET.parse(file_path)
        return True
    except ET.ParseError:
        return False

def check_tier_structure(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    # Example check: ensure there is at least one TIER element
    return bool(root.find('TIER'))

def check_annotations_have_values(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    for tier in root.findall('TIER'):
        for annotation in tier.findall('.//ALIGNABLE_ANNOTATION'):
            if annotation.find('ANNOTATION_VALUE') is None:
                return False
    return True

if __name__ == '__main__':
    application.run(debug=True)
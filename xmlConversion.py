import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re  # Import regular expressions module

# Constants
INPUT_FILE = 'newman_report.xml'  # Input file in the job workspace
OUTPUT_FILE = 'xray_compatible_report.xml'  # Output file in the job workspace
TESTSUITE_TAG = 'testsuite'
TESTCASE_TAG = 'testcase'
FAILURE_TAG = 'failure'
PROPERTIES_TAG = 'properties'
PROPERTY_TAG = 'property'

def read_xml_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def parse_testsuites(content):
    start_index = content.find('<testsuites')
    if start_index == -1:
        raise ValueError('No <testsuites> element found in the XML file.')
    relevant_content = content[start_index:]
    return ET.fromstring(relevant_content)

def create_output_structure(root):
    root_name = root.get('name')
    # Add the 'classname' attribute with the same value as the 'name' attribute
    output_root = ET.Element('testsuites', {
        'name': root_name,
        'tests': str(len(root.findall(TESTSUITE_TAG))),
        'time': '0.0',
        'classname': root_name  # Set 'classname' equal to 'name'
    })
    return output_root

def add_testsuite(output_root, testsuite):
    suite_name = testsuite.get('name')
    suite_id = testsuite.get('id')
    suite_tests = int(testsuite.get('tests'))
    suite_failures = int(testsuite.get('failures'))
    suite_errors = int(testsuite.get('errors'))
    suite_time = float(testsuite.get('time'))

    new_testsuite = ET.SubElement(output_root, TESTSUITE_TAG, {
        'name': suite_name,
        'id': suite_id,
        'timestamp': testsuite.get('timestamp'),
        'tests': str(suite_tests),
        'failures': str(suite_failures),
        'errors': str(suite_errors),
        'time': str(suite_time)
    })

    return suite_time, new_testsuite, suite_failures

def format_classname_with_space(classname):
    # Convert to uppercase and insert a space between the alphabetic and numeric parts
    match = re.match(r'([A-Za-z]+)(\d+)', classname)  # Match alphabetic part followed by numeric part
    if match:
        # Add space between the two parts and return uppercase version
        formatted_classname = f"{match.group(1).upper()} {match.group(2)}"
    else:
        # If no match, just return the uppercase version of the classname
        formatted_classname = classname.upper()
    return formatted_classname

def add_testcase(new_testsuite, testcase, suite_name):
    test_name = testcase.get('name')
    test_classname = testcase.get('classname')

    # Format classname by converting to uppercase and adding space between alphabetic and numeric parts
    test_classname_formatted = format_classname_with_space(test_classname)

    test_time = testcase.get('time')

    new_testcase = ET.SubElement(new_testsuite, TESTCASE_TAG, {
        'classname': test_classname_formatted,  # Use the formatted classname
        'name': test_name,
        'time': test_time
    })

    properties = ET.SubElement(new_testcase, PROPERTIES_TAG)
    ET.SubElement(properties, PROPERTY_TAG, {
        'name': 'test_key',
        'value': suite_name
    })

    failure_elements = testcase.findall(FAILURE_TAG)
    if failure_elements:
        status = 'FAIL'
        ET.SubElement(properties, PROPERTY_TAG, {
            'name': 'status',
            'value': status
        })
        for failure in failure_elements:
            failure_message = failure.get('message')
            failure_element = ET.SubElement(new_testcase, FAILURE_TAG, {
                'type': failure.get('type'),
                'message': failure_message
            })
            failure_text = ''.join(failure.itertext()).strip()
            failure_element.text = failure_text.splitlines()[0]
    else:
        status = 'PASS'
        ET.SubElement(properties, PROPERTY_TAG, {
            'name': 'status',
            'value': status
        })
        success_message = ET.SubElement(new_testcase, 'success_message')
        success_message.text = f'Test validation: "{test_name}" passed successfully.'

def pretty_print_xml(element):
    xml_str = ET.tostring(element, encoding='utf-8', method='xml')
    parsed_xml = minidom.parseString(xml_str)
    return parsed_xml.toprettyxml(indent='    ')

def write_output_file(output_root, file_path):
    with open(file_path, 'w') as xml_file:
        xml_file.write(pretty_print_xml(output_root))

def main():
    content = read_xml_file(INPUT_FILE)
    root = parse_testsuites(content)
    output_root = create_output_structure(root)

    total_time = 0.0

    for testsuite in root.findall(TESTSUITE_TAG):
        suite_time, new_testsuite, suite_failures = add_testsuite(output_root, testsuite)
        total_time += suite_time

        for testcase in testsuite.findall(TESTCASE_TAG):
            add_testcase(new_testsuite, testcase, testsuite.get('name'))

    output_root.set('time', str(total_time))
    write_output_file(output_root, OUTPUT_FILE)
    print(f'XML file created successfully: {OUTPUT_FILE}')

if __name__ == '__main__':
    main()

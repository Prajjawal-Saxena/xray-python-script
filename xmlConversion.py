import xml.etree.ElementTree as ET
from xml.dom import minidom

# Constants
INPUT_FILE = 'newman_report.xml'  # Replace with your actual file name
OUTPUT_FILE = 'xray_compatible_report.xml'  # Output file name
if not os.path.exists(INPUT_FILE):
    print(f"Input file '{INPUT_FILE}' does not exist. Skipping conversion.")
    exit(1)
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
        raise ValueError("No <testsuites> element found in the XML file.")
    relevant_content = content[start_index:]
    return ET.fromstring(relevant_content)

def create_output_structure(root):
    root_name = root.get('name')
    output_root = ET.Element('testsuites', {
        'name': root_name,
        'tests': str(len(root.findall(TESTSUITE_TAG))),
        'time': '0.0'
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

def add_testcase(new_testsuite, testcase, suite_name):
    test_name = testcase.get('name')
    test_classname = testcase.get('classname')
    test_time = testcase.get('time')

    new_testcase = ET.SubElement(new_testsuite, TESTCASE_TAG, {
        'classname': test_classname,
        'name': test_name,
        'time': test_time
    })

    properties = ET.SubElement(new_testcase, PROPERTIES_TAG)
    ET.SubElement(properties, PROPERTY_TAG, {
        'name': 'test_key',
        'value': suite_name
    })

    # Check for failures in the testcase
    failure_elements = testcase.findall(FAILURE_TAG)
    if failure_elements:
        # If there are failures, set status to FAIL
        status = 'FAIL'
        ET.SubElement(properties, PROPERTY_TAG, {
            'name': 'status',
            'value': status
        })
        # Add failure details
        for failure in failure_elements:
            failure_message = failure.get('message')
            failure_element = ET.SubElement(new_testcase, FAILURE_TAG, {
                'type': failure.get('type'),
                'message': failure_message
            })
            failure_text = ''.join(failure.itertext()).strip()
            failure_element.text = failure_text.splitlines()[0]  # Only take the first line of text
    else:
        # If no failures, set status to PASS
        status = 'PASS'
        ET.SubElement(properties, PROPERTY_TAG, {
            'name': 'status',
            'value': status
        })
        # Add a success message as a child element instead of an attribute
        success_message = ET.SubElement(new_testcase, 'success_message')
        success_message.text = f'Test validation: "{test_name}" passed successfully.'

def pretty_print_xml(element):
    xml_str = ET.tostring(element, encoding='utf-8', method='xml')
    parsed_xml = minidom.parseString(xml_str)
    return parsed_xml.toprettyxml(indent="    ")

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
    print(f"XML file created successfully: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

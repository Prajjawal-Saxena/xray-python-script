import csv
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom  # For pretty-printing the XML


# Function to create an XML element for a single test case
def create_testcase_element(request_name, executed, assertions, failures, failed_count, example_index=None):
    testcase = ET.Element('testcase')
    testcase.set('classname', request_name)  # Use requestName as classname
    testcase.set('name', request_name)  # Test ID

    # Add example index if provided (for multiple executions of the same test)
    if example_index is not None:
        testcase.set('example', str(example_index))

    # Create <properties> block
    properties = ET.SubElement(testcase, 'properties')

    # Add test_key property (requestName)
    test_key = ET.SubElement(properties, 'property')
    test_key.set('name', 'test_key')
    test_key.set('value', request_name)

    # Set status property (PASS/FAIL)
    status_property = ET.SubElement(properties, 'property')
    status_property.set('name', 'status')
    if failed_count > 0:
        status_property.set('value', 'FAIL')
        failure_message = ET.SubElement(testcase, 'failure')
        failure_message.set('type', 'AssertionFailure')
        failure_message.set('message', failures)  # Add the failure reason as an attribute
        failure_message.text = f"Failed {failed_count} times."  # Add the failure count in text
    else:
        status_property.set('value', 'PASS')
        # Success message with dynamic content
        success_message = ET.SubElement(testcase, 'success_message')
        success_message.set('message', executed)  # Use dynamic success message from CSV data
        success_message.text = f"Validation passed successfully."

    return testcase


# Function to convert CSV to JUnit XML with properties and updated messages
def csv_to_junit_xml(csv_file, xml_output_file):
    # Create the root element <testsuites>
    testsuites = ET.Element('testsuites')
    testsuite = ET.SubElement(testsuites, 'testsuite')
    testsuite.set('name', 'CSV Test Results')  # Customize your suite name

    # Open and read the CSV file
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        test_cases = {}

        # Group data by requestName (as a test case)
        for row in reader:
            request_name = row['requestName']
            executed = row['executed']
            failed = row['failed']
            total_assertions = int(row['totalAssertions'])
            failed_count = int(row['failedCount'])

            # If the requestName repeats, treat it as a single test with multiple executions
            if request_name not in test_cases:
                test_cases[request_name] = {
                    'executions': [],  # List to store multiple executions (examples)
                }

            # Append each execution (example) for the same requestName
            test_cases[request_name]['executions'].append({
                'executed': executed,  # Capture the executed success message
                'assertions': total_assertions,
                'failures': failed,
                'failed_count': failed_count,
            })

        # Add each test case and its executions (examples) to the XML
        for request_name, details in test_cases.items():
            # Handle multiple executions for the same requestName
            for idx, execution in enumerate(details['executions']):
                testcase = create_testcase_element(
                    request_name,
                    execution['executed'],  # Pass dynamic success message
                    execution['assertions'],
                    execution['failures'],
                    execution['failed_count'],
                    example_index=idx + 1  # Example index starts at 1
                )
                testsuite.append(testcase)

    # Convert the ElementTree to a string
    xml_string = ET.tostring(testsuites, encoding='utf-8')

    # Use minidom to pretty-print the XML
    pretty_xml_string = minidom.parseString(xml_string).toprettyxml(indent="  ")

    # Write the pretty-printed XML to the output file
    with open(xml_output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_string)


# Path to the CSV and the output XML
csv_file = 'csv-report.csv'  # Replace with your actual CSV path
xml_output_file = 'xray_report.xml'

# Convert CSV to XML
csv_to_junit_xml(csv_file, xml_output_file)
print(f"JUnit XML report generated: {xml_output_file}")

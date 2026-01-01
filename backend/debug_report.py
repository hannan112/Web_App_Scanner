import sys
import os

# Add current directory to path so we can import scanning
sys.path.append(os.getcwd())

from scanning.report_generator import ReportGenerator

mock_scan = {
    'target_url': 'http://example.com',
    'created_at': '2023-10-27',
    'scan_type': 'comprehensive',
    'summary': {
        'critical_count': 1,
        'high_count': 1,
        'medium_count': 1,
        'low_count': 1,
        'info_count': 1
    },
    'vulnerabilities': [
        {'name': 'Vuln 1', 'severity': 'high', 'description': 'desc', 'solution': 'fix'},
        {'name': 'Vuln 2', 'severity': 'low', 'description': 'desc', 'solution': 'fix'},
        # Add a mock False Positive
        {'name': 'FP Vuln', 'severity': 'medium', 'description': 'fp desc', 'solution': 'fp fix', 
         'other_info': '{"ml_is_fp": true}'}
    ],
    'project': {'name': 'Test Project'}
}

print("Attempting to generate report...")
try:
    generator = ReportGenerator(mock_scan)
    pdf_buffer = generator.generate()
    print("Successfully generated PDF of size:", len(pdf_buffer.getvalue()))
except Exception as e:
    import traceback
    traceback.print_exc()

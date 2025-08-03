from Wappalyzer import Wappalyzer, WebPage
import requests

print("Importing Wappalyzer successful!")

# Initialize Wappalyzer
try:
    wappalyzer = Wappalyzer.latest()
    print("Wappalyzer initialized successfully")
    
    # Create webpage object
    url = "https://example.com/"
    print(f"Requesting {url}...")
    response = requests.get(url)
    print(f"Got response with status code: {response.status_code}")
    
    webpage = WebPage.new_from_response(response)
    print("Created WebPage object")
    
    # Analyze
    print("Analyzing with Wappalyzer...")
    result = wappalyzer.analyze(webpage)
    print(f"Detected technologies: {result}")
    print("Test completed successfully!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
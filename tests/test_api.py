import requests
import time
import json

API_BASE_URL = "http://localhost:8080"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health_check():
    """Test health check endpoints"""
    print_section("Testing Health Check Endpoints")
    
    print("\n1. Testing GET /")
    response = requests.get(f"{API_BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n2. Testing GET /hello")
    response = requests.get(f"{API_BASE_URL}/hello")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

def test_single_prediction():
    """Test single prediction endpoint"""
    print_section("Testing Single Prediction")
    
    print("\n1. Submitting single prediction...")
    payload = {
        "summary": "Refactor database layer to use async connections",
        "description": "We should refactor our database layer to support async connections for better performance"
    }
    
    response = requests.post(f"{API_BASE_URL}/predictions", json=payload)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Task ID: {result['task_id']}")
    print(f"   Status: {result['status']}")

    task_id = result['task_id']
    print(f"\n2. Polling for result (task_id: {task_id})...")
    
    max_attempts = 30
    for i in range(max_attempts):
        time.sleep(1)
        response = requests.get(f"{API_BASE_URL}/predictions/{task_id}")
        status_result = response.json()
        
        print(f"   Attempt {i+1}: Status = {status_result['status']}")
        
        if status_result['status'] == 'SUCCESS':
            print(f"Prediction: {status_result.get('result', {})}")
            break
        elif status_result['status'] == 'FAILURE':
            print(f"Failed: {status_result.get('error', 'Unknown error')}")
            break
    else:
        print(f"Timeout after {max_attempts} seconds")

def test_batch_prediction():
    """Test batch prediction endpoint"""
    print_section("Testing Batch Prediction")
    
    print("\n1. Submitting batch prediction...")
    payload = {
        "issues": [
            {
                "summary": "Change button color to blue",
                "description": "User reported that the submit button should be blue"
            },
            {
                "summary": "Implement caching layer with Redis",
                "description": "Add Redis caching layer to improve performance"
            },
            {
                "summary": "Fix typo in error message",
                "description": "There's a typo in the login error message"
            }
        ]
    }
    
    response = requests.post(f"{API_BASE_URL}/predictions/batch", json=payload)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Task IDs: {result['task_ids']}")
    print(f"   Number of tasks: {len(result['task_ids'])}")
    
    print(f"\n2. Polling for batch results...")
    task_ids = result['task_ids']
    
    completed = 0
    for attempt in range(30):
        time.sleep(2)
        all_complete = True
        
        for i, task_id in enumerate(task_ids):
            response = requests.get(f"{API_BASE_URL}/predictions/{task_id}")
            status_result = response.json()
            
            if status_result['status'] == 'SUCCESS':
                if attempt == 0:
                    print(f"   Task {i+1}: {status_result.get('result', {})}")
                completed += 1
            elif status_result['status'] in ['PENDING', 'STARTED']:
                all_complete = False
        
        if all_complete:
            print(f"All {len(task_ids)} predictions complete!")
            break
    else:
        print(f"Some predictions did not complete in time")

def test_search():
    """Test search endpoint"""
    print_section("Testing Search Endpoint")
    
    print("\n1. Searching for 'refactor'...")
    response = requests.get(f"{API_BASE_URL}/issues/search", params={"keyword": "refactor"})
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Total found: {result['total']}")
        print(f"   Returned: {len(result['results'])} results")
        
        if result['results']:
            print(f"\n   First result:")
            first = result['results'][0]
            print(f"     Summary: {first.get('summary', 'N/A')}")
            print(f"     Label: {first.get('label', 'N/A')}")
    else:
        print(f"   Error: {response.json()}")

def test_labeled_submission():
    """Test labeled data submission endpoint"""
    print_section("Testing Labeled Data Submission (Bonus)")
    
    print("\n1. Submitting labeled issue...")
    payload = {
        "summary": "Migrate authentication to OAuth2",
        "description": "We need to migrate from basic auth to OAuth2 for better security",
        "label": "ADD"
    }
    
    response = requests.post(f"{API_BASE_URL}/issues/labeled", json=payload)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f" {result['message']}")
        print(f"   Issue ID: {result['id']}")
        print(f"   Label: {result['label']}")
    else:
        print(f"   Error: {response.json()}")

    print("\n2. Getting labeled data count...")
    response = requests.get(f"{API_BASE_URL}/issues/labeled/count")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Total labeled: {result['total']}")
        print(f"   ADD: {result['add_count']}")
        print(f"   non-ADD: {result['non_add_count']}")

def test_statistics():
    """Test statistics endpoint"""
    print_section("Testing Statistics Endpoint")
    
    response = requests.get(f"{API_BASE_URL}/stats")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Total issues: {result['total_issues']}")
        print(f"   Total labeled: {result['total_labeled']}")
        print(f"   API version: {result['api_version']}")

def main():
    """Run all tests"""
    print("\nStarting API Tests")
    print(f"   Target: {API_BASE_URL}")
    
    try:
        test_health_check()
        test_single_prediction()
        test_batch_prediction()
        test_search()
        test_labeled_submission()
        test_statistics()
        
        print_section("All Tests Complete!")
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to API")
        print(f"   Make sure the API is running at {API_BASE_URL}")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import requests
import json

try:
    response = requests.get('http://127.0.0.1:8000/api/panchang/today/?date=2025-12-25&language=te', timeout=5)
    if response.status_code == 200:
        data = response.json()
        print('API Response Keys:', list(data.keys()))
        if 'sections' in data:
            for section in data['sections']:
                print(f'Section: {section["title"]}')
                if 'సాంప్రదాయ పంచాంగం' in section["title"]:
                    print('Traditional section found!')
                    print('Items:', section['items'])
                    break
        else:
            print('No sections found in response')
    else:
        print(f'API returned status code: {response.status_code}')
        print('Response:', response.text[:200])
except Exception as e:
    print(f'Error: {e}')
    print('API server may not be running. Please start the Django server first.')



import json
import random
import uuid
from datetime import datetime

def generate_mongodb_data(num_records=50):
    """Generate mock MongoDB-style data with irregular schema.
    
    Args:
        num_records: Number of records to generate.
        
    Returns:
        List of dictionaries representing MongoDB documents.
    """
    data = []
    
    common_keys = ['_id', 'created_at', 'status']
    varied_keys = ['user', 'metadata', 'tags', 'history', 'config', 'preferences', 'analytics']
    
    for i in range(num_records):
        record = {
            '_id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'status': random.choice(['active', 'pending', 'archived', 'deleted'])
        }
        
        num_keys = random.randint(1, len(varied_keys))
        selected_keys = random.sample(varied_keys, num_keys)
        
        for key in selected_keys:
            if key == 'user':
                record['user'] = {
                    'name': f"User_{i}",
                    'email': f"user{i}@example.com"
                }
                if random.choice([True, False]):
                    record['user']['verified'] = True
                    
            elif key == 'metadata':
                meta = {'version': 1}
                if random.choice([True, False]):
                    meta['source'] = 'web'
                if random.choice([True, False]):
                    meta['context'] = {'ip': '127.0.0.1', 'browser': 'Chrome'}
                record['metadata'] = meta
                
            elif key == 'tags':
                record['tags'] = [f"tag_{random.randint(1, 10)}" for _ in range(random.randint(1, 5))]
                
            elif key == 'history':
                record['history'] = []
                for _ in range(random.randint(1, 3)):
                    record['history'].append({
                        'action': random.choice(['login', 'logout', 'view']),
                        'ts': int(datetime.now().timestamp())
                    })
                    
            elif key == 'config':
                record['config'] = {
                    'theme': random.choice(['dark', 'light']),
                    'notifications': random.choice([True, False])
                }
                
            elif key == 'preferences':
                record['preferences'] = {}
                if random.choice([True, False]):
                    record['preferences']['lang'] = 'en'
                if random.choice([True, False]):
                    record['preferences']['timezone'] = 'UTC'
                    
            elif key == 'analytics':
                record['analytics'] = {
                    'visits': random.randint(1, 100),
                    'score': random.random()
                }

        data.append(record)
        
    return data

if __name__ == "__main__":
    data = generate_mongodb_data()
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    with open(os.path.join(data_dir, 'mongodb_irregular.json'), 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Generated benchmarks/data/mongodb_irregular.json with {len(data)} records")

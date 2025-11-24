#!/usr/bin/env python3
"""
Fetch Internet Data - Downloads random data from public APIs
Generates fresh test data from various public APIs for benchmarking.
"""

import json
import urllib.request
from pathlib import Path


def fetch_json(url):
    """Fetch JSON from URL."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"  ⚠️ Failed to fetch {url}: {e}")
        return None


def main():
    """Fetch internet data from various APIs."""
    data_dir = Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("Fetching Internet Data from Public APIs")
    print("=" * 80)
    
    sources = []
    
    # 1. JSONPlaceholder - Posts
    print("\n1. JSONPlaceholder Posts...")
    posts = fetch_json('https://jsonplaceholder.typicode.com/posts')
    if posts:
        # Take first 100
        posts_subset = posts[:100]
        with open(data_dir / 'internet_posts.json', 'w') as f:
            json.dump({"posts": posts_subset}, f)
        sources.append(("JSONPlaceholder Posts", len(posts_subset), len(json.dumps({"posts": posts_subset}))))
        print(f"  ✅ Saved {len(posts_subset)} posts")
    
    # 2. JSONPlaceholder - Users
    print("\n2. JSONPlaceholder Users...")
    users = fetch_json('https://jsonplaceholder.typicode.com/users')
    if users:
        with open(data_dir / 'internet_users.json', 'w') as f:
            json.dump({"users": users}, f)
        sources.append(("JSONPlaceholder Users", len(users), len(json.dumps({"users": users}))))
        print(f"  ✅ Saved {len(users)} users")
    
    # 3. Random User API
    print("\n3. Random User API...")
    random_users = fetch_json('https://randomuser.me/api/?results=50')
    if random_users and 'results' in random_users:
        with open(data_dir / 'internet_random_users.json', 'w') as f:
            json.dump(random_users, f)
        sources.append(("Random Users", len(random_users['results']), len(json.dumps(random_users))))
        print(f"  ✅ Saved {len(random_users['results'])} random users")
    
    # 4. GitHub Public Repos
    print("\n4. GitHub Public Repositories...")
    repos = fetch_json('https://api.github.com/repositories?per_page=20')
    if repos:
        with open(data_dir / 'internet_github_repos.json', 'w') as f:
            json.dump({"repos": repos}, f)
        sources.append(("GitHub Repos", len(repos), len(json.dumps({"repos": repos}))))
        print(f"  ✅ Saved {len(repos)} repositories")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"\nSource                    | Records | JSON Size")
    print("-" * 60)
    for name, count, size in sources:
        print(f"{name:25} | {count:7} | {size:9,} bytes")
    
    print(f"\n✅ Saved {len(sources)} internet datasets to: {data_dir}")


if __name__ == '__main__':
    main()

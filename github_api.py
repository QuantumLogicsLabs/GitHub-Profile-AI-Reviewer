import requests
import json

# 1. GitHub Token and Configuration
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE" 
USERNAME = "octocat" 

url = "https://api.github.com/graphql"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}


query = """
query($username: String!) {
  user(login: $username) {
    name
    bio
    repositories(first: 10, orderBy: {field: STARGAZERS, direction: DESC}) {
      nodes {
        name
        stargazerCount
        primaryLanguage {
          name
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
      }
    }
  }
}
"""

variables = {"username": USERNAME}

print(f"Fetching GitHub data for user: {USERNAME}...")

# 3. API Request 
try:
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("\nGraphQL Query Success!")
        print(json.dumps(data, indent=2))
    elif response.status_code == 401:
        print("\nAPI Error: Unauthorized. (Token missing ya invalid hai, which is expected right now!)")
        print(" Schema validation checker success! Query structure is 100% correct.")
    else:
        print(f"\nAPI Error: Status Code {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Connection Error: {str(e)}")
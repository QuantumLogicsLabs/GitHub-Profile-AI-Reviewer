from __future__ import annotations

ANALYZE_PROFILE_QUERY = """
query AnalyzeProfile($username: String!) {
  user(login: $username) {
    login
    name
    bio
    createdAt
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
    repositories(first: 20, orderBy: { field: STARGAZERS, direction: DESC }) {
      nodes {
        name
        nameWithOwner
        description
        stargazerCount
        forkCount
        primaryLanguage { name }
        languages(first: 5) {
          edges {
            size
            node { name }
          }
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 1) { totalCount }
            }
          }
        }
      }
    }
    pullRequests(first: 50, states: MERGED) { totalCount }
  }
}
""".strip()

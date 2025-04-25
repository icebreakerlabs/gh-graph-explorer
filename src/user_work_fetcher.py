from typing import Optional
import os
import datetime
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport


# Define the GraphQL query as a string
USER_WORK_QUERY = """
query getUserWork($username:String!, $owner:String!, $repo:String!, $sinceIso: DateTime!, $prsCreatedQuery:String!, $prContributionsQuery:String!, $issueCommentsQuery:String!, $discussionsCreatedQuery:String!, $discussionsInvolvedQuery:String!) {
  repository(owner: $owner, name: $repo) {
      ...repo
  }
  prsCreated:search(type: ISSUE, query: $prsCreatedQuery, first: 20) {
    edges {
      node {
        ... on PullRequest {
          title
          createdAt
          url
        }
      }
    }
  }
  prReviewsAndCommits:search(type: ISSUE, query: $prContributionsQuery, first: 20) {
    edges {
      node {
        ... on PullRequest {
          createdAt
          title
          url
          author {
            login
          }
          reviews(first: 10, author:$username) {
            nodes {
              state
              createdAt
              url
            }
          }
        }
      }
    }
  }
  issueComments:search(type: ISSUE, query: $issueCommentsQuery, first: 50) {
    nodes {
      ... on Issue {
        title
        url
        comments(last:30) {
          nodes {
            createdAt
            author {
              login
            }
            url
          }
        }
      }
    }
  }
  discussionsCreated:search(type: DISCUSSION, query: $discussionsCreatedQuery, first: 20) {
    nodes {
      ... on Discussion {
        author {
          login
        }
        title
        createdAt
        number
        url
        repository {
          nameWithOwner
        }
      }
    }
  }
  discussionComments:search(type: DISCUSSION, query: $discussionsInvolvedQuery, first: 20) {
    nodes {
      ... on Discussion {
        title
        url
        comments(last:30) {
          nodes {
              author {
              login
            }
            bodyText
            createdAt
            url
          }
        }
        repository {
          nameWithOwner
        }
      }
    }
  }
}

fragment repo on Repository {
    issues(last: 20, filterBy: {createdBy: $username, since: $sinceIso}, orderBy:{ field: CREATED_AT, direction:DESC }) {
      nodes {
        createdAt
        title
        url
      }
    }
  }
"""


class UserWorkFetcher:
    def __init__(self, github_token: str = None):
        """
        Initialize the UserWorkFetcher with a GitHub token.

        Args:
            github_token: GitHub personal access token with appropriate permissions.
                          If None, will try to use GITHUB_TOKEN from environment variables.
        """
        if github_token is None:
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token is None:
                raise ValueError(
                    "GitHub token not provided and GITHUB_TOKEN environment variable not set"
                )

        # Set up the transport with the GitHub GraphQL API endpoint
        transport = AIOHTTPTransport(
            url="https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {github_token}"},
        )

        # Create the client
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        self.query = gql(USER_WORK_QUERY)

    def _build_prs_created_query(
        self, username: str, since_date: datetime.datetime
    ) -> str:
        """Build query for PRs created by the user"""
        return f"author:{username} is:pr updated:>={since_date.strftime('%Y-%m-%d')}"

    def _build_pr_contributions_query(
        self, username: str, since_date: datetime.datetime
    ) -> str:
        """Build query for PRs the user contributed to but didn't author"""
        return f"involves:{username} is:pr updated:>={since_date.strftime('%Y-%m-%d')}"  # -author:{username}

    def _build_issue_comments_query(
        self, username: str, since_date: datetime.datetime
    ) -> str:
        """Build query for issues with user comments"""
        return f"commenter:{username} is:issue updated:>={since_date.strftime('%Y-%m-%d')}"  # -author:{username}

    def _build_discussions_created_query(
        self, username: str, since_date: datetime.datetime
    ) -> str:
        """Build query for discussions created by the user"""
        return f"author:{username} is:discussion updated:>={since_date.strftime('%Y-%m-%d')}"

    def _build_discussions_involved_query(
        self, username: str, since_date: datetime.datetime
    ) -> str:
        """Build query for discussions the user is involved in but didn't create"""
        return f"involves:{username} is:discussion updated:>={since_date.strftime('%Y-%m-%d')}"  # -author:{username}

    async def get(
        self,
        username: str,
        owner: str,
        repo: str,
        since_iso: str = None,
        days: int = 30,
    ) -> dict:
        """
        Simplified method to get user's GitHub work data.

        Args:
            username: GitHub username
            owner: Repository owner
            repo: Repository name
            since_iso: DateTime string in ISO format for filtering by date
                      (if None, will use current date minus days)
            days: Number of days to look back if since_iso is not provided

        Returns:
            The GraphQL query results as a dictionary
        """
        # Calculate since_date if since_iso is not provided
        if since_iso is None:
            today = datetime.datetime.now()
            since_date = today - datetime.timedelta(days=days)
            since_iso = since_date.isoformat()
        else:
            # Parse the ISO string to a datetime object for building queries
            since_date = datetime.datetime.fromisoformat(
                since_iso.replace("Z", "+00:00")
            )

        # Build all query strings
        name_with_owner_query = f"repo:{owner}/{repo} "
        prs_created_query = name_with_owner_query + self._build_prs_created_query(
            username, since_date
        )
        pr_contributions_query = (
            name_with_owner_query
            + self._build_pr_contributions_query(username, since_date)
        )
        issue_comments_query = name_with_owner_query + self._build_issue_comments_query(
            username, since_date
        )
        discussions_created_query = (
            name_with_owner_query
            + self._build_discussions_created_query(username, since_date)
        )
        discussions_involved_query = (
            name_with_owner_query
            + self._build_discussions_involved_query(username, since_date)
        )

        # Execute the query with built parameters
        return await self.execute_query(
            username=username,
            owner=owner,
            repo=repo,
            since_iso=since_iso,
            prs_created_query=prs_created_query,
            pr_contributions_query=pr_contributions_query,
            issue_comments_query=issue_comments_query,
            discussions_created_query=discussions_created_query,
            discussions_involved_query=discussions_involved_query,
        )

    async def execute_query(
        self,
        username: str,
        owner: str,
        repo: str,
        since_iso: str,
        prs_created_query: str,
        pr_contributions_query: str,
        issue_comments_query: str,
        discussions_created_query: str,
        discussions_involved_query: str,
    ) -> dict:
        """
        Execute the getUserWork GraphQL query with the provided parameters.

        Args:
            username: GitHub username
            owner: Repository owner
            repo: Repository name
            since_iso: DateTime string in ISO format for filtering by date
            prs_created_query: Search query for PRs created by user
            pr_contributions_query: Search query for PRs the user contributed to
            issue_comments_query: Search query for issues with user comments
            discussions_created_query: Search query for discussions created by user
            discussions_involved_query: Search query for discussions the user is involved in

        Returns:
            The GraphQL query results as a dictionary
        """
        variables = {
            "username": username,
            "owner": owner,
            "repo": repo,
            "sinceIso": since_iso,
            "prsCreatedQuery": prs_created_query,
            "prContributionsQuery": pr_contributions_query,  # Add missing parameter
            "issueCommentsQuery": issue_comments_query,
            "discussionsCreatedQuery": discussions_created_query,
            "discussionsInvolvedQuery": discussions_involved_query,
        }

        # Execute the query
        result = await self.client.execute_async(self.query, variable_values=variables)
        return result

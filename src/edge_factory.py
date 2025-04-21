from typing import Dict, Any, Generator
from .edge import Edge

class EdgeFactory:
    """
    Class to extract GitHub work data results and generate graph edges.
    """
    def __init__(self, data: Dict[str, Any], username: str = "anonymous"):
        """
        Initialize EdgeFactory with the data returned from UserWorkFetcher.
        
        Args:
            data: Dictionary containing GitHub work data results
            username: GitHub username to associate with edges
        """
        self.data = data
        self.username = username
    
    def generate_edges(self) -> Generator[Edge, None, None]:
        """
        Generate edges from GitHub work data.
        
        Yields:
            Edge objects representing GitHub activity
        """
        # Process issues created by user
        if self.data.get('repository', {}).get('issues', {}).get('nodes'):
            for issue in self.data['repository']['issues']['nodes']:
                url = issue.get('url')
                edge = Edge(
                    edge_type='issue_created',
                    title=issue.get('title'),
                    created_at=issue.get('createdAt'),
                    login=self.username,
                    url=url,
                    parent_url=None
                )
                yield edge
        
        # Process pull requests created
        if self.data.get('prsCreated', {}).get('edges'):
            for pr_edge in self.data['prsCreated']['edges']:
                pr = pr_edge.get('node', {})
                url = pr.get('url')
                edge = Edge(
                    edge_type='pr_created',
                    title=pr.get('title'),
                    created_at=pr.get('createdAt'),
                    login=self.username,
                    url=url,
                    parent_url=None
                )
                yield edge
        
        # Process issue comments
        for issue in self.data.get('issueComments', {}).get('nodes', []):
            if issue.get('comments', {}).get('nodes'):
                for comment in issue['comments']['nodes']:
                    edge = Edge(
                        edge_type='issue_comment',
                        title=None,
                        created_at=comment.get('createdAt'),
                        login=comment.get('author', {}).get('login'),
                        url=comment.get('url'),
                        parent_url=issue.get('url')
                    )
                    yield edge
        
        # Process pull request reviews and commits
        for pr_edge in self.data.get('prReviewsAndCommits', {}).get('edges', []):
            pr = pr_edge.get('node', {})
            pr_url = pr.get('url')
            
            # Process reviews in the pull request
            for review in pr.get('reviews', {}).get('nodes', []):
                for comment in review.get('comments', {}).get('nodes', []):
                    yield Edge(
                        edge_type='pr_review',
                        title=None,
                        created_at=comment.get('createdAt'),
                        login=self.username,
                        url=comment.get('url'),
                        parent_url=pr_url
                    )
                
            # Process reviews in the pull request
            if pr.get('reviews', {}).get('nodes'):
                for review in pr['reviews']['nodes']:
                    edge = Edge(
                        edge_type='pr_review',
                        title=None,
                        created_at=review.get('createdAt'),
                        login=self.username,
                        url=review.get('url'),
                        parent_url=pr_url
                    )
                    yield edge
        

        # Process discussions created
        if self.data.get('discussionsCreated', {}).get('nodes'):
            for discussion in self.data['discussionsCreated']['nodes']:
                url = discussion.get('url')
                edge = Edge(
                    edge_type='discussion_created',
                    title=discussion.get('title'),
                    created_at=discussion.get('createdAt'),
                    login=self.username,
                    url=url,
                    parent_url=None
                )
                yield edge
        
        # Process discussion comments
        if self.data.get('discussionComments', {}).get('nodes'):
            for discussion in self.data['discussionComments']['nodes']:
                if discussion.get('comments', {}).get('nodes'):
                    for comment in discussion['comments']['nodes']:
                        edge = Edge(
                            edge_type='discussion_comment',
                            created_at=comment.get('createdAt'),
                            login=comment.get('author', {}).get('login'),
                            url=comment.get('url'),
                            title=None,
                            parent_url=discussion.get('url')
                        )
                        yield edge

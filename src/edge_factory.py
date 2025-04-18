from typing import Dict, Any, Generator, Optional, List
from edge import Edge

class EdgeFactory:
    """
    Class to extract GitHub work data results and generate graph edges.
    """
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize EdgeFactory with the data returned from UserWorkFetcher.
        
        Args:
            data: Dictionary containing GitHub work data results
        """
        self.data = data
    
    def generate_edges(self) -> Generator[Edge, None, None]:
        """
        Generate edges from GitHub work data.
        
        Yields:
            Edge objects representing GitHub activity
        """
        # Process issues created by user
        

        if self.data.get('repository', {}).get('issues', {}).get('nodes'):
            for issue in self.data['repository']['issues']['nodes']:
                login = issue.get('author', {}).get('login', 'anonymous')
                url = issue.get('url')
                edge = Edge(
                    edge_type='issue_created',
                    title=issue.get('title'),
                    created_at=issue.get('createdAt'),
                    login=login,
                    url=url
                )
                yield edge
        
        # Process pull requests created

        if self.data.get('prsCreated', {}).get('edges'):
            for pr_edge in self.data['prsCreated']['edges']:
                pr = pr_edge.get('node', {})
                login = pr.get('author', {}).get('login', 'anonymous')
                url = pr.get('url')
                edge = Edge(
                    edge_type='pr_created',
                    title=pr.get('title'),
                    created_at=pr.get('createdAt'),
                    login=login,
                    url=url
                )
                yield edge
                
        

        # Process issue comments
        if self.data.get('issueComments', {}).get('nodes'):
            for issue in self.data['issueComments']['nodes']:
                if issue.get('comments', {}).get('nodes'):
                    for comment in issue['comments']['nodes']:
                        if comment.get('author', {}).get('login'):
                            login = comment['author']['login']
                            issue_url = issue.get('url')
                            comment_url = comment.get('url')
                            edge = Edge(
                                edge_type='issue_comment',
                                title=None,
                                created_at=comment.get('createdAt'),
                                login=login,
                                url=comment_url
                            )
                            yield edge
        
        # Process discussions created
        if self.data.get('discussionsCreated', {}).get('nodes'):
            for discussion in self.data['discussionsCreated']['nodes']:
                if discussion.get('author', {}).get('login'):
                    login = discussion['author']['login']
                    url = discussion.get('url')
                    edge = Edge(
                        edge_type='discussion_created',
                        title=discussion.get('title'),
                        created_at=discussion.get('createdAt'),
                        login=login,
                        url=url
                    )
                    yield edge
        

        # Process discussion comments
        if self.data.get('discussionComments', {}).get('nodes'):
            for discussion in self.data['discussionComments']['nodes']:
                if discussion.get('comments', {}).get('nodes'):
                    for comment in discussion['comments']['nodes']:
                        if comment.get('author', {}).get('login'):
                            login = comment['author']['login']
                            discussion_url = discussion.get('url')
                            comment_url = comment.get('url')
                            edge = Edge(
                                edge_type='discussion_comment',
                                created_at=comment.get('createdAt'),
                                login=login,
                                url=comment_url,
                                title=None
                            )
                            yield edge

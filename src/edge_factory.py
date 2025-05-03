from typing import Dict, Any, Generator, List
from .edge import Edge

from re import findall


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
        self.at_mention_pattern = r"(?<!\w)@([\w\/]+)"

    def extract_mentioned_users(self, text: str) -> List[str]:
        return list(findall(self.at_mention_pattern, text))

    def process_issues(self) -> Generator[Edge, None, None]:
        if self.data.get("repository", {}).get("issues", {}).get("nodes"):
            for issue in self.data["repository"]["issues"]["nodes"]:
                url = issue.get("url")
                edge = Edge(
                    edge_type="issue_created",
                    title=issue.get("title"),
                    created_at=issue.get("createdAt"),
                    login=self.username,
                    url=url,
                    parent_url=None,
                )
                yield edge

                for mention in self.extract_mentioned_users(issue.get("bodyText", "")):
                    edge = Edge(
                        edge_type="issue_mentioned",
                        title=issue.get("title"),
                        created_at=issue.get("createdAt"),
                        login=mention,
                        url=url,
                        parent_url=None,
                    )
                    yield edge

    def process_issue_comments(self) -> Generator[Edge, None, None]:
        for issue in self.data.get("issueComments", {}).get("nodes", []):
            if issue.get("comments", {}).get("nodes"):
                for comment in issue["comments"]["nodes"]:
                    edge = Edge(
                        edge_type="issue_comment",
                        title=issue.get("title"),
                        created_at=comment.get("createdAt"),
                        login=comment.get("author", {}).get("login"),
                        url=comment.get("url"),
                        parent_url=issue.get("url"),
                    )
                    yield edge

                    for mention in self.extract_mentioned_users(
                        comment.get("bodyText", "")
                    ):
                        edge = Edge(
                            edge_type="issue_comment_mentioned",
                            title=comment.get("title"),
                            created_at=comment.get("createdAt"),
                            login=mention,
                            url=comment.get("url"),
                            parent_url=issue.get("url"),
                        )
                        yield edge

    def proccess_prs(self) -> Generator[Edge, None, None]:
        if self.data.get("prsCreated", {}).get("edges"):
            for pr_edge in self.data["prsCreated"]["edges"]:
                pr = pr_edge.get("node", {})
                url = pr.get("url")
                edge = Edge(
                    edge_type="pr_created",
                    title=pr.get("title"),
                    created_at=pr.get("createdAt"),
                    login=self.username,
                    url=url,
                    parent_url=None,
                )
                yield edge

                for mention in self.extract_mentioned_users(pr.get("bodyText", "")):
                    edge = Edge(
                        edge_type="pr_mentioned",
                        title=pr.get("title"),
                        created_at=pr.get("createdAt"),
                        login=mention,
                        url=url,
                        parent_url=None,
                    )
                    yield edge

    def process_pr_reviews(self) -> Generator[Edge, None, None]:
        for pr_edge in self.data.get("prReviewsAndCommits", {}).get("edges", []):
            pr = pr_edge.get("node", {})
            # Process reviews in the pull request
            for review in pr.get("reviews", {}).get("nodes", []):
                yield Edge(
                    edge_type="pr_review_" + review.get("state", "").lower(),
                    title=pr.get("title"),
                    created_at=review.get("createdAt"),
                    login=self.username,
                    url=review.get("url"),
                    parent_url=pr.get("url"),
                )

                for mention in self.extract_mentioned_users(review.get("bodyText", "")):
                    edge = Edge(
                        edge_type="pr_comment_mentioned",
                        title=pr.get("title"),
                        created_at=review.get("createdAt"),
                        login=mention,
                        url=review.get("url"),
                        parent_url=pr.get("url"),
                    )
                    yield edge

    def process_discussions(self) -> Generator[Edge, None, None]:
        if self.data.get("discussionsCreated", {}).get("nodes"):
            for discussion in self.data["discussionsCreated"]["nodes"]:
                url = discussion.get("url")
                edge = Edge(
                    edge_type="discussion_created",
                    title=discussion.get("title"),
                    created_at=discussion.get("createdAt"),
                    login=self.username,
                    url=url,
                    parent_url=None,
                )
                yield edge

                for mention in self.extract_mentioned_users(
                    discussion.get("bodyText", "")
                ):
                    edge = Edge(
                        edge_type="discussion_mentioned",
                        title=discussion.get("title"),
                        created_at=discussion.get("createdAt"),
                        login=mention,
                        url=discussion.get("url"),
                        parent_url=None,
                    )
                    yield edge

    def process_discussion_comments(self) -> Generator[Edge, None, None]:
        """
        Process discussions from GitHub work data.

        Yields:
            Edge objects representing GitHub activity
        """
        for discussion in self.data.get("discussionComments", {}).get("nodes", []):
            for comment in discussion.get("comments", {}).get("nodes", []):
                edge = Edge(
                    edge_type="discussion_comment",
                    created_at=comment.get("createdAt"),
                    login=comment.get("author", {}).get("login"),
                    url=comment.get("url"),
                    title=discussion.get("title"),
                    parent_url=discussion.get("url"),
                )
                yield edge

                for mention in self.extract_mentioned_users(
                    comment.get("bodyText", "")
                ):
                    edge = Edge(
                        edge_type="discussion_comment_mentioned",
                        title=discussion.get("title"),
                        created_at=discussion.get("createdAt"),
                        login=mention,
                        url=comment.get("url"),
                        parent_url=discussion.get("url"),
                    )
                    yield edge

    def generate_edges(self) -> Generator[Edge, None, None]:
        """
        Generate edges from GitHub work data.

        Yields:
            Edge objects representing GitHub activity
        """
        yield from self.process_issues()
        yield from self.process_issue_comments()
        yield from self.proccess_prs()
        yield from self.process_pr_reviews()
        yield from self.process_discussions()
        yield from self.process_discussion_comments()

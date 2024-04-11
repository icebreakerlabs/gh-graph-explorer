import os
import networkx as nx
import csv

from github import Github
from github import Auth
from datetime import datetime


class Link:
    def clean_url(self, url):
        return url.replace('https://api.github.com/repos/', '')

    def is_bot(self, user):
        if user in ['ninesappbot']:
            return True
        if user.endswith('[bot]'):
            return True
        if user.endswith('-bot'):
            return True
        return False
    
class CommentLink(Link):
    def __init__(self, subject):
        self.subject = subject

    def predicate(self):
        return "commented"

    def updated_at(self):
        return self.subject.updated_at
    
    def user(self):
        return self.subject.user.login
    
    def is_from_bot(self):
        return self.is_bot(self.user())    

    def target(self):
        return self.clean_url(self.subject.issue_url)

    def issue_url(self):
        return self.subject.issue_url
    
    def issue_number(self):
        return int(self.subject.issue_url.split('/')[-1])

    def to_csv_row(self):
        return [self.user(), self.target(), self.predicate(), self.updated_at(), self.is_from_bot()]

    def to_edge(self):
        return (self.user(), self.target())

    def attributes(self):
        return {"updated_at": self.updated_at(), "is_from_bot": self.is_from_bot(), "predicate": self.predicate()}


class IssueLink(Link):
    def __init__(self, subject):
        self.subject = subject

    def predicate(self):
        return "author"

    def updated_at(self):
        return self.subject.updated_at

    def user(self):
        return self.subject.user.login
    
    def target(self):
        return self.clean_url(self.subject.url)

    def is_from_bot(self):
        return self.is_bot(self.user())    

    def to_csv_row(self):
        return [self.user(), self.target(), self.predicate(), self.updated_at(), self.is_from_bot()]

    def to_edge(self):
        return (self.user(), self.target())

    def attributes(self):
        return {"updated_at": self.updated_at(), "is_from_bot": self.is_from_bot(), "predicate": self.predicate()}

class RowLink:
    
    def __init__(self, row):
        self.row = row 

    def to_edge(self):
        return (self.row["source"], self.row["target"])

    def attributes(self):
        return {"updated_at": self.row["updated_at"], "is_from_bot": self.row["is_from_bot"], "predicate": self.row["predicate"]}


class GraphCollector():
    def __init__(self, repository_names=[], since=None):
        self.repository_names = repository_names
        self.since = since
        self.issues_link_cache = set()
        auth = Auth.Token(os.getenv('GH_TOKEN'))
        self.github = Github(auth=auth)
    
    def stream(self):
        for repository_name in self.repository_names:
            repository = self.github.get_repo(repository_name)
            for comment in repository.get_issues_comments(sort='updated', direction='asc', since=self.since):
                comment_link = CommentLink(comment)
                yield comment_link
                if comment_link.issue_url in self.issues_link_cache:
                    continue
                self.issues_link_cache.add(comment.issue_url)
                issue = repository.get_issue(comment_link.issue_number())
                yield IssueLink(issue)



class CSVGraphCollector:
    def __init__(self, filename):
        self.filename = filename

    def stream(self):
        with open(self.filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["source","target","predicate","updated_at","is_from_bot"])
            next(reader, None) # Skip the first row
            for row in reader:
                yield RowLink(row)


class GraphBuilder():
    def __init__(self, collector=None, team=[]):
        self.collector = collector
        # Setup Graph
        self.G = nx.Graph()
        for user in team:
            self.G.add_node(user, size=6, color='green')

    def build_and_write(self):
        with open("graph-record-"+datetime.now().strftime("%Y-%m-%d") +'.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["source","target","predicate","updated_at","is_from_bot"])
            for link in self.collector.stream():
                writer.writerow(link.to_csv_row())
            
    def build(self):
        for link in self.collector.stream():
            self.G.add_edge(*link.to_edge(), **link.attributes())

        return self.G

if __name__ == "__main__":
    
    collector = GraphCollector(repository_names=['github/mail-replies'], since=datetime(2024, 4, 10))
    team = ['geramirez', 'jlord', 'abeaumont', 'andrejusk', 'mrtazz', 'franciscoj', 'gerbenjacobs', 'jezcommits', 'jhbabon' ]
    graph_builder = GraphBuilder(
        collector=collector,
        team=team
    )
    graph_builder.build_and_write()


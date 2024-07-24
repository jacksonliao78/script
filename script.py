import requests
import getpass
import json
import time

class MassArchive:
    def __init__(self, address, name, password):
        self.url_search = "%s/rest/api/2/search" % address
        self.url_archive = "%s/rest/api/2/issue/archive" % address
        self.url_config = "%s/rest/api/2/application-properties/advanced-settings" % address
        self.auth_val = (name, password)

        self.validate_auth()

    def validate_auth(self):
        session = requests.Session()
        resp = session.get(self.url_search, auth=self.auth_val, verify=False)
        if resp.status_code != 200:
            raise Exception(f"Authentication failed: {resp.status_code}, {resp.text}")

    def search_issues(self, jql, limit):
        session = requests.session()
        issues_to_archive = set()
        max_per_request = 25 #self.get_limit_per_request(session)
        start_at = 0

        # this loop gathers all issues that meet jql query until reaching specified limit
        while len(issues_to_archive) < limit or limit == -1:
            data = {'jql': jql, 'startAt': start_at, 'maxResults': limit, 'fields': ['key']}
            resp = session.post(self.url_search, json=data, auth=self.auth_val, verify=False)
            
        
            
            if limit == -1 :
                issues_ = json.loads(resp.text)['issues']
            else:
                issues_ = json.loads(resp.text)['issues'][:min(limit, limit - len(issues_to_archive))]

            for issue in issues_:
                issues_to_archive.add(issue['key'])

            start_at += max_per_request

            if len(issues_) < max_per_request:
                break

        return issues_to_archive

    #this is not used
    def get_limit_per_request(self, session):
        print (self.url_config)
        resp = session.get(self.url_config, auth=self.auth_val, verify=False)
        return int(
            list(filter(lambda row: row['id'] == "jira.search.views.default.max", json.loads(resp.text)))[0]['value'])

    def archive_issues(self, jql, limit=-1):
        issue_keys = list(self.search_issues(jql, limit))
        batch_size = 100

        for i in range(0, len(issue_keys), batch_size):
            batch = issue_keys[i:i+batch_size]
            self.archive_specific(batch)
            time.sleep(2)  

    def archive_specific(self, issue_keys):
        session = requests.session()
        response = session.post(self.url_archive, json=issue_keys, auth=self.auth_val, stream=True, verify=False)

        for line in response.iter_lines():
            print('Issue %s is Archived' % line.decode("utf-8").split(',')[0])

    def print_issues(self, jql, limit):
        issue_keys = list(self.search_issues(jql, limit))
        print("Issues found:")
        for key in issue_keys:
            print(key)

def main():
    url = input("url address: ")
    name = input("username: ")
    password = getpass.getpass("password: ")
    jql_query = input("JQL query: ")
    limit = input("limit (type -1 to archive all found): ")
    

    test = MassArchive(url, name, password)
    #test.print_issues(jql_query, int(limit))
    test.archive_issues(jql_query, int(limit))

if __name__ == "__main__":
    main()

#url -> https://jira.sdlc.redcross.us/
#jql -> (issuefunction in parentsOf("issuetype in subTaskIssueTypes() and statusCategory = Done") AND statuscategory = Done AND updated < 2022-07-01) OR (issuefunction not in parentsOf("issuetype in subTaskIssueTypes()") and issuetype != Test AND statuscategory = Done AND updated < 2022-07-01) ORDER BY updated DESC

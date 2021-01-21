""" Fetch issues that match given parameters """
__author__ = "Kristian Berg"
__copyright__ = "Copyright (c) 2018 Axis Communications AB"
__license__ = "MIT"

from urllib.parse import quote
import urllib.request as url
import json
import requests
import os
import argparse
import io
import sys
import time
import re
import config

def fetch_issues(owner, repo):
    """ Fetch all issues from given repository """
    request = "https://api.github.com/repos/"+args.owner+"/"+args.repo+"/issues"

    # using api_token to incrase rate limit
    # NOTE: This is not necessary, just recommended
    # Rate limit with token: 30 requests per minute
    # Without token: 10 requests per minute
    api_token = config.api_key

    '''
        Searching for issues includes both pull requests and issues
        Parameters that can be passed:
            page: The page to start searching on
            per_page: # of results per page
            state: the state of the issue/pull request
                - closed - closed issues
                - open - open issues
            type: 
                - issue - issues
                - pr - pull request
            labels: the label associated with the issue/pull request
    '''

    startpage = 1
    params = {'page':startpage, 'per_page':100, 'state':'closed', 'labels':'bug'}
    headers = {'Authorization': 'token %s' % api_token}
    timeout = time.time() + 5 # 5 second timeout between requests
    # Initial reuqest
    r = requests.get(request, params=params, headers=headers)
    # This directory will be created wherever the script is being ran from
    os.makedirs('issues/', exist_ok=True)

    issues = []
    pr = []

    # Loop through each page of issues
    while True:
        if time.time() > timeout:
            # This is put inside the loop so that the page numebr will be updated
            
            timeout = time.time() + 5 # 5 second timeout between requests
            try:
                json_obj = json.loads(r.text)
                # go through each json dictionary and split up pull requests from issues
                for data in json_obj:
                    result = re.search("pull", data['html_url'])
                    if (result):
                        pr.append(data)
                    else:
                        issues.append(data)
                        
                # if there are no links we can assume that the rate limit was reached, and thus we will provide a checkpoint for next time
                if len(r.links) == 0:
                    print(dir(r))
            except Exception as e:
                print("An error has occurred")
                print(e)
                break

            print("Successful page requests: %d" % (startpage))

            # look for:
            # <https://api.github.com/search/code?q=addClass+user%3Amozilla&page=2>;rel="next"
            # in the links returned from the API which indicate that there are more issues
            # To view these links, you can also use the curl command, i.e. curl -I "https://api.github.com/search/code?q=addClass+user:mozilla"
            # the -I command indicates that you are only interested in the headers, not the content
            if 'next' in r.links:
                startpage += 1
                print("Next link: ", r.links['next']['url'])
                request = r.links['next']['url']
                r = requests.get(request, headers=headers)
            else:
                break
    if len(issues) > 0:
        with open("issues/issue_results.json", 'a') as f:
            f.write(json.dumps(issues, indent=2))
    if len(pr) > 0:
        with open("issues/pr_results.json", 'a') as f:
            f.write(json.dumps(pr, indent=2))
    print("Task completed")
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Get issues associated with a Github repository.')
    parser.add_argument('--owner', '-o', type=str, required=True,
                    help='The owner/organization associated with a repository')
    parser.add_argument('--repo', '-r', type=str, required=True,
                    help='The repository name')

    args = parser.parse_args()

    fetch_issues(args.owner, args.repo, )

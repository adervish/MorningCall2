from flask import Flask, request, redirect
import requests
import os
from flask import Flask, abort, request, Blueprint, render_template, abort
from uuid import uuid4
import requests
import requests.auth
import urllib
# Replace these with your Zoom OAuth app credentials
#!/usr/bin/env python
REDIRECT_URI = "http://localhost:65010/zoom_callback"
REFRESH_TOKEN = None
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

zoom_page = Blueprint('zoom_page', __name__,
                        template_folder='templates')

@zoom_page.route('/zoom')
def homepage():
    #tokens = refresh_token(REFRESH_TOKEN)
    #return "Your user info is: %s" % list_recordings(tokens['access_token'])

    text = '<a href="%s">Authenticate with Zoom</a>'
    return text % make_authorization_url()

def make_authorization_url():
    # Generate a random string for the state parameter
    # Save it for use later to prevent xsrf 
    # attacks
    
    params = {"client_id": CLIENT_ID,
              "response_type": "code",
              "redirect_uri": REDIRECT_URI}
    url = "https://zoom.us/oauth/authorize?" + urllib.parse.urlencode(params)
    return url

@zoom_page.route('/zoom_callback')
def zoom_callback():
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    
    code = request.args.get('code')
    tokens = get_token(code)
    access_token = tokens['access_token']
    #tokens = refresh_token(tokens['refresh_token'])
    # Note: In most cases, you'll want to store the access token, in, say,
    # a session for use in other parts of your web app.
    meetings = []
    json = get_meeting_recordings(access_token, "85001327653")
    print(json)
    return json
    #json = list_recordings(access_token)

    #for m in json['meetings']:
    #    meetings.append(m['recording_files'][2]['download_url'])
    #return get_transcript(access_token, meetings[0])
    #return meetings

def get_meeting_recordings(access_token, meeting_id):
    headers= {"Authorization": "bearer " + access_token}
    response = requests.get(f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings", headers=headers)
    me_json = response.json()
    return me_json

def get_transcript(access_token, meeting_url):
    print (meeting_url)
    headers= {"Authorization": "bearer " + access_token}
    response = requests.get(meeting_url, headers=headers)
    print (response.content)
    me_json = response.content
    return me_json    

def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": REDIRECT_URI}

    response = requests.post("https://zoom.us/oauth/token",
                             auth=client_auth,
                             data=post_data)
    token_json = response.json()
    print( f"Refresh Token={token_json['refresh_token']}")
    return token_json
    
def get_username(access_token):
    
    headers= {"Authorization": "bearer " + access_token}
    response = requests.get("https://api.zoom.us/v2/users/me", headers=headers)
    me_json = response.json()
    return me_json

def refresh_token(refresh_token):
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {"grant_type": "refresh_token",
                 "refresh_token": refresh_token}
    response = requests.post("https://zoom.us/oauth/token", auth=client_auth,
                             data=post_data)
    
    me_json = response.json()
    return me_json

def list_recordings(access_token):
    headers= {"Authorization": "bearer " + access_token}
    response = requests.get("https://api.zoom.us/v2/users/me/recordings", headers=headers)
    me_json = response.json()
    return me_json

if __name__ == '__main__':
    app.run(debug=True, port=65010)

import os

DEBUG=False
DEBUG=True

ASSETS_PATH=os.environ['OPENSHIFT_REPO_DIR']
DOMAIN=os.environ['OPENSHIFT_APP_DNS']

# Slight complication, real openshift requires this go through port 8000
# https://www.openshift.com/blogs/paas-websockets
if 'OPENSHIFT_APP_NAME' in os.environ:
    WEBSOCKET_URL="ws://%s:8000/" % DOMAIN
else:
    WEBSOCKET_URL="ws://%s/" % DOMAIN

SERVER_PORT=int(os.environ['OPENSHIFT_PYTHON_PORT'])
SERVER_IP=os.environ['OPENSHIFT_PYTHON_IP']

db_name = 'players.db'

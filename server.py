import socket
import signal
import sys
import random

# Read a command line argument for the port where the server
# must run.
port = 8080
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")
hostname = socket.gethostname()

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)

### Contents of pages we will serve.
# Login form
login_form = """
   <form action = "http://%s" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
"""
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = """
   <h1>Welcome!</h1>
   <form action="http://%s" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
"""

#### Helper functions
# Printing.
def print_value(tag, value):
    print("Here is the", tag)
    print("\"\"\"")
    print(value)
    print("\"\"\"")
    print()

# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)

def parseRequest(reqBody):

    if not reqBody:
        raise ValueError("Empty request body")
    
    pairs = reqBody.split('&')
    formData = {}

    for pair in pairs:
        if '=' not in pair:
            raise ValueError("Badly formed request body: missing '='")
        
        key, value = pair.split('=', 1)

        if not key:
            raise ValueError("Missing request body key")
        if not value:
            raise ValueError(f"Missing value for key '{key}'")

        formData[key] = value
    
    return formData

def validateUser(user, password):
    return user in credentialsDB and credentialsDB[user] == password


# TODO: put your application logic here!
# Read login credentials for all the users
# Read secret data of all the users

#extract the token from a complex cookie header it supports multiple cookies
def getCookieToken(cookieHeader):
    cookies = cookieHeader.split(';')
    for cookie in cookies:
        if 'token=' in cookie:
            return cookie.strip().split('token=')[-1]
    return None


# Initialize Database
credentialsDB = {}
secretsDB = {}
cookieDB = {}

# Populating credentials db
with open('passwords.txt', 'r') as credFile:
    for line in credFile:
        line = line.strip()
        if line:
            user, password = line.split()
            credentialsDB[user] = password

# Populating secrets db
with open('secrets.txt', 'r') as secFile:
    for line in secFile:
        line = line.strip()
        if line:
            user, secret = line.split()
            secretsDB[user] = secret


### Loop to accept incoming HTTP connections and respond.
while True:
    client, addr = sock.accept()
    req = client.recv(1024)

    # Let's pick the headers and entity body apart
    header_body = req.decode().split('\r\n\r\n')
    headers = header_body[0]
    body = '' if len(header_body) == 1 else header_body[1]
    
    print_value('headers', headers)
    print_value('entity body', body)

    # try:
    #     formData = parseRequest(body)
    #     username = formData.get('username')
    #     password = formData.get('password')
    # except ValueError as e:
    #     print("Error parsing request:", e)
    #     # Return Error page or login page here

    #     # Just skip any further processing


    # if not username or not password:
    #     print("Missing username OR password")
        

    # TODO: Put your application logic here!
    # Parse headers and body and perform various actions

    # OPTIONAL TODO:
    # Set up the port/hostname for the form's submit URL.
    # If you want POSTing to your server to
    # work even when the server and client are on different
    # machines, the form submit URL must reflect the `Host:`
    # header on the request.
    # Change the submit_hostport variable to reflect this.
    # This part is optional, and might even be fun.
    # By default, as set up below, POSTing the form will
    # always send the request to the domain name returned by
    # socket.gethostname().
    # submit_hostport = "%s:%d" % (hostname, port)
    
    submit_hostport = "10.74.178.48"
    
    # You need to set the variables:
    # (1) `html_content_to_send` => add the HTML content you'd
    # like to send to the client.
    # Right now, we just send the default login page.
    html_content_to_send = login_page % submit_hostport
    # But other possibilities exist, including
    # html_content_to_send = (success_page % submit_hostport) + <secret>
    # html_content_to_send = bad_creds_page % submit_hostport
    # html_content_to_send = logout_page % submit_hostport
    
    # (2) `headers_to_send` => add any additional headers
    # you'd like to send the client?
    # Right now, we don't send any extra headers.

    html_content_to_send = ''
    headers_to_send = ''
    
    #attempting case E
    try:
        formData = parseRequest(body)
        if formData.get("action") == "logout":
            headers_to_send = "Set-Cookie: token=; expires=Thu, 01 Jan 1970 00:00:00 GMT\r\n"
            html_content_to_send = logout_page % submit_hostport
            response  = 'HTTP/1.1 200 OK\r\n' + headers_to_send
            response += 'Content-Type: text/html\r\n\r\n' + html_content_to_send
            client.send(response.encode())
            client.close()
            print("Logout completed!")
            continue
    except:
        pass

    cookieHeader = ''
    
    for line in headers.splitlines():
        if line.startswith("Cookie:"):
            cookieHeader = line
            break

    if cookieHeader:
        token = getCookieToken(cookieHeader)
        #token = cookieHeader.split("token=")[-1].strip()

        # Valid case, if token exists in our cookieDB, we have a valid cookie
        if token in cookieDB:
            username = cookieDB[token]
            secret = secretsDB.get(username, "No secret available :/")
            html_content_to_send = (success_page % submit_hostport) + secret
        else:
            # Invalid cookie, serve bad credentials case
            html_content_to_send = bad_creds_page % submit_hostport
    
    else:
        try:
            formData = parseRequest(body)
            username = formData.get('username')
            password = formData.get('password')
        except ValueError as e:
            print("Error parsing request:", e)
            # Return Error page or login page here

            # Just skip any further processing
            html_content_to_send = login_page % submit_hostport
        else:
            if username is None and password is None:
                html_content_to_send = login_page % submit_hostport
            elif (username is None) != (password is None):
                html_content_to_send = bad_creds_page % submit_hostport
            elif validateUser(username, password):
                randVal = random.getrandbits(64)
                token = str(randVal)
                cookieDB[token] = username
                headers_to_send = f"Set-Cookie: token={token}\r\n"
                secret = secretsDB.get(username, "No secret available :/")
                html_content_to_send = (success_page % submit_hostport) + secret
            else:
                html_content_to_send = bad_creds_page % submit_hostport

    # Default to login page
    if not html_content_to_send:
        html_content_to_send = login_page % submit_hostport

    # Construct and send the final response
    response  = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response)    
    client.send(response.encode())
    client.close()
    
    print("Served one request/connection!")
    print()

# We will never actually get here.
# Close the listening socket
sock.close()

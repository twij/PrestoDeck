import sys

import urequests as requests
import usocket as socket
import ujson as json

class SpotifyWebApiClient:
    def __init__(self, session):
        self.session = session

    def play(self, context_uri=None, uris=None, offset=None, position_ms=None):
        request_body = {}
        if context_uri is not None:
            request_body['context_uri'] = context_uri
        if uris is not None:
            request_body['uris'] = list(uris)
        if offset is not None:
            request_body['offset'] = offset
        if position_ms is not None:
            request_body['position_ms'] = position_ms

        self.session.put(
            url='https://api.spotify.com/v1/me/player/play',
            json=request_body,
        )

    def pause(self):
        self.session.put(
            url='https://api.spotify.com/v1/me/player/pause',
        )
    
    def toggle_shuffle(self, state):
        value = "true" if state else "false"
        self.session.put(
            url=f'https://api.spotify.com/v1/me/player/shuffle?state={value}',
        )
    
    def toggle_repeat(self, state):
        value = "track" if state else 'off'
        self.session.put(
            url=f'https://api.spotify.com/v1/me/player/repeat?state={value}',
        )
    
    def next(self):
        self.session.post(
            url='https://api.spotify.com/v1/me/player/next',
        )

    def previous(self):
        self.session.post(
            url='https://api.spotify.com/v1/me/player/previous',
        )

    def current_playing(self):
        return self.session.get(
            url='https://api.spotify.com/v1/me/player',
        )
    
    def recently_played(self):
        return self.session.get(
            url='https://api.spotify.com/v1/me/player/recently-played?limit=1',
        )

    def devices(self):
        response = self.session.get(
            url='https://api.spotify.com/v1/me/player/devices',
        )
        for device in response['devices']:
            yield Device(**device)

class Device:
    def __init__(
        self,
        id,
        is_active,
        is_private_session,
        is_restricted,
        name,
        type,
        volume_percent,
        **kwargs
    ):
        self.id = id
        self.is_active = is_active
        self.is_private_session = is_private_session
        self.is_restricted = is_restricted
        self.name = name
        self.type = type
        self.volume_percent = volume_percent

    def __repr__(self):
        return 'Device(name={}, type={}, id={})'.format(self.name, self.type, self.id)

class Session:
    def __init__(self, credentials):
        self.credentials = credentials
        self.device_id = credentials['device_id']

    def get(self, url, **kwargs):
        def get_request():
            return requests.get(
                url,
                headers=self._headers(),
                **kwargs,
            )

        return self._execute_request(get_request)

    def put(self, url, json=None, **kwargs):
        # Workaround for urequests not sending "Content-Length" on empty data
        if json is None:
            json = {}

        def put_request():
            return requests.put(
                url=self._add_device_id(url),
                headers=self._headers(),
                json=json,
                **kwargs,
            )

        return self._execute_request(put_request)
    
    def post(self, url, json=None, **kwargs):
        # Workaround for urequests not sending "Content-Length" on empty data
        if json is None:
            json = {}

        def post_request():
            return requests.post(
                url=self._add_device_id(url),
                headers=self._headers(),
                json=json,
                **kwargs,
            )

        return self._execute_request(post_request)

    def _headers(self):
        return {'Authorization': 'Bearer {access_token}'.format(**self.credentials)}

    def _execute_request(self, request):
        response = request()
        if response.status_code == 401:
            error = Session._error_from_response(response)

            if error['message'] == 'The access token expired':
                self._refresh_access_token()
                response = request()  # Retry

        self._check_status_code(response)
        content_type = response.headers.get("content-type")
        if response.content and content_type and content_type.startswith("application/json"):
            return response.json()

    @staticmethod
    def _check_status_code(response):
        if response.status_code >= 400:
            error = Session._error_from_response(response)
            raise SpotifyWebApiError(**error)

    @staticmethod
    def _error_from_response(response):
        try:
            error = response.json()['error']
            message = error['message']
            reason = error.get('reason')
        except (ValueError, KeyError):
            message = response.text
            reason = None
        return {'message': message, 'status': response.status_code, 'reason': reason}

    def _add_device_id(self, url):
        join = '&' if '?' in url else '?'
        return '{path}{join}device_id={device_id}'.format(path=url, join=join, device_id=self.device_id) if self.device_id else url

    def _refresh_access_token(self):
        token_endpoint = "https://accounts.spotify.com/api/token"
        params = dict(
            grant_type="refresh_token",
            refresh_token=self.credentials['refresh_token'],
            client_id=self.credentials['client_id'],
            client_secret=self.credentials['client_secret'],
        )
        response = requests.post(
            token_endpoint,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=urlencode(params),
        )
        self._check_status_code(response)

        tokens = response.json()
        self.credentials['access_token'] = tokens['access_token']
        if 'refresh_token' in tokens:
            self.credentials['refresh_token'] = tokens['refresh_token']

class SpotifyWebApiError(Exception):
    def __init__(self, message, status=None, reason=None):
        super().__init__(message)
        self.status = status
        self.reason = reason

def parse_qs(qs):
    parsed_result = {}
    pairs = parse_qsl(qs)
    for name, value in pairs:
        if name in parsed_result:
            parsed_result[name].append(value)
        else:
            parsed_result[name] = [value]
    return parsed_result

def parse_qsl(qs):
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r = []
    for name_value in pairs:
        if not name_value:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            continue
        if len(nv[1]):
            name = nv[0].replace('+', ' ')
            name = unquote(name)
            value = nv[1].replace('+', ' ')
            value = unquote(value)
            r.append((name, value))
    return r

def quote(s):
    always_safe = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' 'abcdefghijklmnopqrstuvwxyz' '0123456789' '_.-'
    res = []
    for c in s:
        if c in always_safe:
            res.append(c)
            continue
        res.append('%%%x' % ord(c))
    return ''.join(res)

def quote_plus(s):
    s = quote(s)
    if ' ' in s:
        s = s.replace(' ', '+')
    return s

def unquote(s):
    res = s.split('%')
    for i in range(1, len(res)):
        item = res[i]
        try:
            res[i] = chr(int(item[:2], 16)) + item[2:]
        except ValueError:
            res[i] = '%' + item
    return "".join(res)

def unquote_plus(s):
    s = s.replace('+', ' ')
    return unquote(s)

def urlencode(query):
    if isinstance(query, dict):
        query = query.items()
    li = []
    for k, v in query:
        if not isinstance(v, list):
            v = [v]
        for value in v:
            k = quote_plus(str(k))
            v = quote_plus(str(value))
            li.append(k + '=' + v)
    return '&'.join(li)

INITIAL_RESPONSE_TEMPLATE = """\
HTTP/1.0 200 OK
Content-Type: text/html

<h1>Authenticate with Spotify</h1>
1) Go to <a target="_blank" href="https://developer.spotify.com/dashboard/applications">Spotify for Developers</a> and "Create an app"<br>
2) Edit Settings on the app, add "{redirect_uri}" as a Redirect URI and Save<br>
3) Enter Client ID below, submit and then allow the scopes for the app.<br><br>

<form action="/auth-request" method="post">
    client_id: <input type="text" name="client_id" size="34" value="{default_client_id}"><br><br>
    client_secret: <input type="text" name="client_secret" size="34" value="{default_client_secret}"><br><br>
    <input type="submit" value="Submit">
</form>
"""


SELECT_DEVICE_TEMPLATE = """\
HTTP/1.0 200 OK
Content-Type: text/html

<h1>Select device</h1>

<form action="/select-device" method="post">
    {device_list}
    <input type="submit" value="Submit">
</form>
"""


AUTH_REDIRECT_TEMPLATE = """\
HTTP/1.0 302 Found
Location: {url}
"""

NOT_FOUND = """\
HTTP/1.0 404 NOT FOUND

"""

DONE_RESPONSE = """\
HTTP/1.0 200 OK
Content-Type: text/html

Setup completed successfully!
"""

def setup_wizard(default_client_id='', default_client_secret='', default_device_id=''):
    s = socket.socket()

    # Binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo("0.0.0.0", 8080)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://{myip}:8080/".format(myip=myip()))

    redirect_uri = None
    client_id = None
    client_secret = None
    credentials = None
    device_selected = False
    spotify_client = None

    while not device_selected:
        client_sock, _ = s.accept()
        client_stream = client_sock

        req = client_stream.readline().decode()
        content_length = None

        while True:
            h = client_stream.readline().decode()
            if h.startswith("Host: "):
                host = h[6:-2]
                redirect_uri = 'http://{host}/auth-response/'.format(host=host)
            if h.startswith("Content-Length: "):
                content_length = int(h[16:-2])
            if h == "" or h == "\r\n":
                break

        def write_response(resp):
            client_stream.write(resp.encode())
            client_stream.close()

        if req.startswith("GET / "):
            write_response(
                INITIAL_RESPONSE_TEMPLATE.format(
                    redirect_uri=redirect_uri,
                    default_client_id=default_client_id,
                    default_client_secret=default_client_secret,
                )
            )

        elif req.startswith("POST /auth-request"):
            authorization_endpoint = 'https://accounts.spotify.com/authorize'
            form_values = parse_qs(client_stream.read(content_length).decode())
            client_id = form_values['client_id'][0]
            client_secret = form_values['client_secret'][0]
            params = dict(
                client_id=client_id,
                response_type='code',
                redirect_uri=redirect_uri,
                scope='user-read-playback-state user-modify-playback-state user-read-recently-played',
            )
            url = "{path}?{query}".format(path=authorization_endpoint, query=urlencode(params))
            write_response(AUTH_REDIRECT_TEMPLATE.format(url=url))

        elif req.startswith("GET /auth-response"):
            authorization_code = parse_qs(req[4:-11].split('?')[1])['code'][0]
            credentials = refresh_token(authorization_code, redirect_uri, client_id, client_secret)
            spotify_client = SpotifyWebApiClient(Session(credentials))
            template = """<input type="radio" name="device_id" value="{id}" {checked}> {name}<br>"""
            device_list_html = [
                template.format(id='', checked='checked' if not default_device_id else '', name='All devices')
            ]
            for device in spotify_client.devices():
                checked = 'checked' if device.id == default_device_id else ''
                device_list_html.append(template.format(id=device.id, checked=checked, name=device.name))
            write_response(SELECT_DEVICE_TEMPLATE.format(device_list=''.join(device_list_html)))

        elif req.startswith("POST /select-device"):
            response = client_stream.read(content_length).decode()
            device_id = parse_qs(response).get('device_id')
            if device_id:
                device_id = device_id[0]
            credentials['device_id'] = device_id
            spotify_client.session.device_id = device_id
            write_response(DONE_RESPONSE)
            device_selected = True
        else:
            write_response(NOT_FOUND)

    print("Copy the following line to secrets.py:")
    print(f"SPOTIFY_CREDENTIALS={credentials}")

    return spotify_client

def refresh_token(authorization_code, redirect_uri, client_id, client_secret):
    params = dict(
        grant_type="authorization_code",
        code=authorization_code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
    )

    access_token_endpoint = "https://accounts.spotify.com/api/token"
    response = requests.post(
        access_token_endpoint,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data=urlencode(params),
    )
    tokens = response.json()
    return dict(
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        client_id=client_id,
        client_secret=client_secret,
        device_id=None,
    )

def myip():
    try:
        import network
        return network.WLAN(network.STA_IF).ifconfig()[0]
    except ImportError:
        return "<my host>"
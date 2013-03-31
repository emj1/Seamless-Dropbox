import dropbox
import webbrowser
import pickle

### Configuration ###
dropbox_folder = 'Dropbox/'
path_to_dropbox_folder = {
    'def': 'path/to/Dropbox/',
    'mac': 'path/to/Dropbox/',
    'ios': '',
}

# those you can get from
# Dropbox developer website
APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = 'dropbox'

force_token_request = False
TOKEN_FILENAME = 'Dropbox.token'
### End of configuration ###


def to_dropbox_path(path):
    """
    converts absolute path to path that can be provided to dropbox API
    """
    dropbox_idx = path.find(dropbox_folder)
    if dropbox_idx == -1:
        return path
    return path[dropbox_idx + len(dropbox_folder):]


def to_absolute_path(dropbox_path, on_what='def'):
    """
    converts path starting in dropbox folder to absolute path
    using path_to_dropbox_folder dictionary
    """
    return path_to_dropbox_folder[on_what] + dropbox_path


# ensure that all paths end with /
if dropbox_folder[-1] != '/':
    dropbox_folder += '/'

for key in path_to_dropbox_folder:
    if path_to_dropbox_folder[key] != '/':
        path_to_dropbox_folder[key] += '/'


# create dropbox session
sess = dropbox.session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)


# request access token and get user to
# auhorize it
def _request_token():
    request_token = sess.obtain_request_token()
    url = sess.build_authorize_url(request_token)
    request_token = sess.obtain_request_token()
    url = sess.build_authorize_url(request_token)

    # Make the user sign in and authorize this token
    webbrowser.open(url)
    print 'press return after you authorize access'
    raw_input()
    access_token = sess.obtain_access_token(request_token)
    return access_token.key, access_token.secret


# save token for future usage
def _save_token(token):
    with open(TOKEN_FILENAME, 'w') as token_file:
        pickle.dump(token, token_file)


# get access token if it's needed
try:
    assert(not force_token_request)
    _token_key, _token_secret = pickle.load(
        open(TOKEN_FILENAME, 'r')
    )
except (AssertionError, IOError):
    _token = _request_token()
    _save_token(_token)
    _token_key, _token_secret = _token


def open(name, mode='r', buffering=None):
    """
    opens file from dropbox, `name` can be path starting in dropbox folder
    or absolute path that has dropbox folder somewhere in it

    `buffering` does nothing, but is declared for compatibility.
    """
    return DropboxFile(name, mode)


class DropboxFile(object):
    """
    Class that wraps parts of Dropbox API to File Object interface.

    Not every method from File interface is implemented, only those
    for writing and reading. Also not every optional argument has sense
    in context of Dropbox, in that case value for this argument can be previded
    but does nothing.

    implemented mathods:
    - close
    - read
    - readline
    - readlines
    - write
    - writelines
    - 'with' statement (__enter__ & __exit__)
    """

    writing_modes = ('w', 'a')
    reading_modes = ('r',)
    modes = writing_modes + reading_modes

    def __init__(self, name, mode='r', buffering=None):
        if not mode in DropboxFile.modes:
            raise ValueError(
                "mode string must be one of {1}, not '{0}'".format(
                    mode,
                    ",".join(
                        "'{0}'".format(m) for m in DropboxFile.modes
                    )
                )
            )
        self.mode = mode
        self.orginal_name = name
        self.name = to_dropbox_path(name)

        self.closed = False

        sess.set_token(_token_key, _token_secret)
        self._client = dropbox.client.DropboxClient(sess)

        if mode == 'r':
            self._file = self._client.get_file(
                self.name
            )
            self.lines = None
        elif mode == 'w':
            self._to_write = ['']
        elif mode == 'a':
            self._to_write = [
                self._client.get_file(self.name).read()
            ]

    def raise_if_not_for_reading(self):
        if not self.mode in DropboxFile.reading_modes:
            raise IOError('File not open for reading')

    def raise_if_not_for_writing(self):
        if not self.mode in DropboxFile.writing_modes:
            raise IOError('File not open for writing')

    def raise_if_closed(self):
        if self.closed:
            raise ValueError("I/O operation on closed file")

    def read(self, size=None):
        self.raise_if_closed()
        self.raise_if_not_for_reading()
        return self._file.read()

    def readlines(self, sizehint=None):
        self.raise_if_closed()
        self.raise_if_not_for_reading()
        return self._file.read().split('\n')

    def readline(self, size=None):
        if self.lines:
            self.lines_idx += 1
            return self.lines[self.lines_idx]

        self.lines = self.readlines()
        self.lines_idx = 0
        return self.lines[self.lines_idx]

    def write(self, text):
        self.raise_if_closed()
        self.raise_if_not_for_writing()
        self._to_write.append(text)

    def writelines(self, sequence):
        self.raise_if_closed()
        self.raise_if_not_for_writing()
        self._to_write += [s + '\n' for s in sequence]

    def close(self):
        self.closed = True
        if self.mode == 'r':
            self._file.close()
            return
        full_file = ''.join(self._to_write)
        self._client.put_file(self.name, full_file, overwrite=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        if exc_type:
            raise exc_type(exc_value)

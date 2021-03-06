import os


class DefaultConfig(object):
    _basedir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__)))))

    DEBUG = True
    TESTING = False

    # Title of your depot
    DEPOT_TITLE = "flask-depot"

    # Change this to something sufficiently random. It's used to secure cookies. Keep it secret!
    SECRET_KEY = "This is not secret enough"

    # This is used to define the database connection you want to use. Make sure to enter the correct details
    # For SQLite (using a relative path)
    # sqlite:///file.db
    #
    # For SQLite (using an absolute path)
    # sqlite:////path/to/file.db
    #
    # For MySQL
    # mysql://username:password@host/databaseName
    #
    # For PostgreSQL:
    # postgresql://username@host/databaseName
    SQLALCHEMY_DATABASE_URI = 'sqlite:///flask-depot.db'
    SQLALCHEMY_RECORD_QUERIES = True

    # Maximum size of uploaded files (in byte)
    MAX_CONTENT_LENGTH = 30 * 1024 * 1024       # 30 megabyte

    # Do not change this!
    CURRENT_DIR = os.path.dirname(os.path.dirname(__file__))

    # Settings for uploaded files
    FILE_RELATIVE = '/static/data/files'
    FILE_DIR = os.path.normpath(CURRENT_DIR + FILE_RELATIVE)
    FILE_MAX_FILESIZE = 30 * 1024 * 1024  # 30 MB
    FILE_EXTENSIONS = ['zip', 'rar']

    # Settings for uploaded preview images
    PREVIEW_RELATIVE = '/static/data/images'
    PREVIEW_DIR = os.path.normpath(CURRENT_DIR + PREVIEW_RELATIVE)
    PREVIEW_MAX_FILESIZE = 1 * 1024 * 1024  # 1 MB
    PREVIEW_MAX_IMGSIZE  = (250, 188)  # (width, height)
    PREVIEW_EXTENSIONS = ['png', 'jpg', 'gif']

    # Prefixes for endpoints/blueprints
    FILE_PREFIX = '/file'
    USER_PREFIX = '/user'
    AUTH_PREFIX = '/auth'
    ADMIN_PREFIX = '/admin'
    SEARCH_PREFIX = '/search'

    # Results per page (search results, administrative lists, etc.)
    RESULTS_PER_PAGE = 15
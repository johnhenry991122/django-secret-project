import io
import os

from six.moves import input
from six.moves import reload_module

from django_secrets.utils import green, red


def create_secrets_package(testing=False):
    try:
        os.stat('secrets')
    except Exception:
        os.mkdir('secrets')
    try:
        os.stat('secrets/__init__.py')
    except OSError:
        with io.open('secrets/__init__.py', 'w', encoding='utf8') as init_file:
            # just touch the file to create a new module
            init_file.close()

    with io.open('secrets/definitions.py', 'w', encoding='utf8') as definitions_file:
        definitions_file.write(u'# coding=utf-8\n\n')
        definitions_file.write(u'# Add your secrets to this list and run manage.py to set their values.\n')
        definitions_file.write(u'# Use them in settings.py like this:\n')
        definitions_file.write(u'# from secrets import secrets\n')
        definitions_file.write(u'# SECRET_KEY = secrets.SECRET_KEY\n\n')
        definitions_file.write(u'SECRET_KEYS = [\n')
        definitions_file.write(u'    # start with your Django secret key like this:\n')
        if testing:
            definitions_file.write(u'    "SECRET_KEY",\n')
            definitions_file.write(u'    "SECOND_SECRET",\n')
        else:
            definitions_file.write(u'    "SECRET_KEY",\n')
        definitions_file.write(u']\n')

    # test for ignore file and create it if needed
    if not os.path.isfile('secrets/.gitignore'):
        with io.open('secrets/.gitignore', 'w', encoding='utf8') as ignore_file:
            ignore_file.write(u'secrets.py\n')

    print(green('\nSecret definitions initialized under secrets/definitions.py'))
    print('Add your secrets there and fill the values on the next use of a manage.py command.\n\n')


def load_definitions():
    try:  # to load the secrets definitions for this project
        from secrets import definitions
    except ImportError:
        # .. otherwise initialize a new secrets package
        create_secrets_package()
        import secrets
        reload_module(secrets)
        from secrets import definitions

    reload_module(definitions)

    return definitions.SECRET_KEYS


def check():

    SECRET_KEYS = load_definitions()

    try:  # to import the existing secrets
        from secrets import secrets as secrets_list
    except ImportError:
        secrets_list = None

    # Configure the project with all secrets found in the definitions list
    # environment vars will be used if available
    filled_blanks = {}
    intro_done = False

    for key in SECRET_KEYS:

        secret = (secrets_list and hasattr(secrets_list, key) and getattr(secrets_list, key)) or os.environ.get(key)
        if secret:
            if not (secrets_list and hasattr(secrets_list, key)):
                print(green('got secret from environment variable (%s)' % key))
            filled_blanks[key] = secret
        else:  # pragma: no cover / inputs ain't possible in the CI
            if not intro_done:
                print(red('\nSecret missing, please fill in the blanks ..\n'))
                intro_done = True

            data = input(key + ': ')
            filled_blanks[key] = data

    with io.open('secrets/secrets.py', 'w', encoding='utf8') as secret_file:

        secret_file.write(u'#  coding=utf-8\n\n')
        for key, value in filled_blanks.items():
            secret_file.write(u'%s = "%s"\n' % (key, value))

    # maybe we had a new value added so refresh the import system
    try:
        from secrets import secrets
    except ImportError:
        import importlib.util
        spec = importlib.util.spec_from_file_location('secrets', 'secrets/secrets.py')
        secrets = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(secrets)

    reload_module(secrets)

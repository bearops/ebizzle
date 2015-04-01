"""Output formatting."""
import myio as io


TEXT = "text"

BASH = "bash"

JSON = "json"

DOCKERENV = "dockerenv"

DEFAULT = "text"


def all():
    return (TEXT, BASH, JSON, DOCKERENV)


def print_dict(dictionary, format_=None):
    """Print a dictionary in a given format. Defaults to text."""

    format_ = format_ or DEFAULT

    if format_ == TEXT:
        for k in sorted(dictionary.keys()):
            io.echo("%s = %s" % (k, dictionary[k]))
    elif format_ == DOCKERENV:
        for k in sorted(dictionary.keys()):
            io.echo("%s=%s" % (k, dictionary[k]))
    elif format_ == BASH:
        for k in sorted(dictionary.keys()):
            io.echo("export %s=%s" % (k, dictionary[k]))
    elif format_ == JSON:
        io.echo(json.dumps(dictionary))


def print_list(list_, format_=None):
    """Print a list in a given format. Defaults to text."""

    format_ = format_ or DEFAULT

    if format_ == TEXT:
        for item in list_:
            io.echo(item)
    elif format_ == JSON:
        io.echo(json.dumps(list_))


def print_profile(profile, format_=None):
    """Print profile header."""

    format_ = format_ or DEFAULT

    if format_ == TEXT:
        io.info("[profile:%s]" % profile)
    elif format_ == BASH:
        io.echo("# profile: %s" % profile)

"""Output formatting."""
import myio as io
import json


TEXT = "text"

BASH = "bash"

JSON = "json"

DOCKERENV = "dockerenv"

DEFAULT = "text"

NAME_VALUE_DICT = "nvdict"  # chronos requires this format for env values


def all():
    return (TEXT, BASH, JSON, DOCKERENV, NAME_VALUE_DICT)


def print_dict(dictionary, format_=None):
    """Print a dictionary in a given format. Defaults to text."""

    format_ = format_ or DEFAULT

    if format_ == TEXT:
        for key, value in iter(sorted(dictionary.iteritems())):
            io.echo("%s = %s" % (key, value))
    elif format_ == DOCKERENV:
        for key, value in iter(sorted(dictionary.iteritems())):
            io.echo("%s=%s" % (key, value))
    elif format_ == BASH:
        for key, value in iter(sorted(dictionary.iteritems())):
            io.echo("export %s=%s" % (key, value))
    elif format_ == JSON:
        io.echo(json.dumps(dictionary))
    elif format_ == NAME_VALUE_DICT:
        io.echo("[")
        for key, value in iter(sorted(dictionary.iteritems())):
            io.echo('{"name": "%s", "value": "%s"},' % (key, value))
        io.echo("]")


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

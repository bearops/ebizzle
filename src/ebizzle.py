#!/usr/bin/env python
import os
import sys
import json
import boto
from boto import beanstalk
import argparse
import subprocess
import ConfigParser

import myio as io


S3_BUILD_DEPS_BUCKET = "dbz-build-deps"

DEFAULT_PROFILE = "test"


class Format(object):
    """Ebizzle output format choices and logic."""

    TEXT = "text"
    BASH = "bash"
    JSON = "json"

    DEFAULT = "text"

    @staticmethod
    def all():
        return (Format.TEXT,
                Format.BASH,
                Format.JSON)

    @staticmethod
    def print_dict(dictionary, format_=None):
        """Print a dictionary in a given format. Defaults to text."""

        format_ = format_ or Format.DEFAULT

        if format_ == Format.TEXT:
            for k in sorted(dictionary.keys()):
                io.echo("%s = %s" % (k, dictionary[k]))
        elif format_ == Format.BASH:
            for k in sorted(dictionary.keys()):
                io.echo("export %s=%s" % (k, dictionary[k]))
        elif format_ == Format.JSON:
            io.echo(json.dumps(dictionary))

    @staticmethod
    def print_list(list_, format_=None):
        """Print a list in a given format. Defaults to text."""

        format_ = format_ or Format.DEFAULT

        if format_ == Format.TEXT:
            for item in list_:
                io.echo(item)
        elif format_ == Format.JSON:
            io.echo(json.dumps(list_))

    @staticmethod
    def print_profile(profile, format_=None):
        """Print profile header."""

        format_ = format_ or Format.DEFAULT

        if format_ == Format.TEXT:
            io.info("[profile:%s]" % profile)
        elif format_ == Format.BASH:
            io.echo("# profile: %s" % profile)


class Action(object):
    """Ebizzle user action choices."""

    CREATE = "create"
    DEPLOY = "deploy"
    LIST = "list"
    PROFILES = "profiles"
    ENV = "env"

    @staticmethod
    def all():
        return (Action.CREATE,
                Action.DEPLOY,
                Action.LIST,
                Action.PROFILES,
                Action.ENV)


def exit(message=None, error=False):
    if message:
        io.error(message)

    sys.exit(int(error))


def panic(message=None):
    exit(message=message, error=True)


def in_git_repository():
    """Is current working dir a git repo?"""

    dev_null = open(os.devnull, "wb")

    return 0 == subprocess.call("git status -s --porcelain",
                                stdout=dev_null,
                                stderr=dev_null,
                                shell=True)


def get_app_name():
    """Extract application's name (assume it's same as CWD dir)."""

    return os.path.split(os.getcwd())[-1]


def get_app_version():
    """Extract application's version from Git (or tag_helper, if exists)."""

    if not in_git_repository():
        panic("Not a git repo, can't obtain application's version.")

    dev_null = open(os.devnull, "wb")

    if os.path.isfile("docker/tag_helper.sh"):
        try:
            name = subprocess.check_output("docker/tag_helper.sh",
                                           stderr=dev_null,
                                           shell=True)
        except subprocess.CalledProcessError:
            pass
        else:
            return name.strip()

    try:
        name = subprocess.check_output("git describe --tags",
                                       stderr=dev_null,
                                       shell=True)
    except subprocess.CalledProcessError:
        panic("Can't obtain app's version. Do you tag, bro?")
    else:
        return name.strip()


def get_config():
    """Return ebizzle's config."""

    config = ConfigParser.ConfigParser()
    config.read(os.path.expanduser("~/.ebizzle/config"))

    return config


def get_credentials(profile):
    """Returns credentials for given profile as a (key, secret) tuple."""

    config = get_config()

    key = config.get(profile, "aws_access_key_id")
    secret = config.get(profile, "aws_secret_access_key")

    return key, secret


def get_profile_names():
    """Get available profile names."""

    return get_config().sections()


def get_s3_conn(profile="production"):
    """Establish and return S3 connection."""

    if profile not in get_profile_names():
        profile = get_profile_names()[0]

    return boto.connect_s3(*get_credentials(profile))


def get_beanstalk(profile):
    """Create and return EB's Layer1."""

    region = beanstalk.regions()[2]
    return beanstalk.layer1.Layer1(*get_credentials(profile),
                                   region=region)


def upload_source_bundle(profile, app, version, source_bundle_path,
                         overwrite=False):
    """Upload EB source bundle to S3."""

    Format.print_profile(profile)
    io.echo("Upload source bundle for %s:%s" % (app, version))

    if not source_bundle_path:
        source_bundle_path = "target/%s-%s.zip" % (app, version)
        io.echo("Source bundle location not given, using default: %s"
                % (source_bundle_path))
    else:
        io.echo("Source bundle location: %s" % (source_bundle_path))

    if not os.path.isfile(source_bundle_path):
        panic("Source bundle not found: %s" % (source_bundle_path))

    source_bundle_path = os.path.expanduser(source_bundle_path)

    s3 = get_s3_conn()

    io.echo("Bucket: %s" % (S3_BUILD_DEPS_BUCKET))
    build_deps_bucket = s3.get_bucket(S3_BUILD_DEPS_BUCKET)

    io.echo("Key: %s/%s-%s.zip" % (app, app, version))
    key = boto.s3.key.Key(build_deps_bucket,
                          "%s/%s-%s.zip" % (app, app, version))

    if not overwrite and key.exists():
        io.echo("Source bundle already exists.")
        return key.key

    with open(source_bundle_path) as f:
        key.set_contents_from_file(f)

    return key.key


def create_version(profile, app, version, s3_bucket, s3_key):
    """Create application's version in EB."""

    Format.print_profile(profile)
    print("Create version %s:%s" % (app, version))
    layer1 = get_beanstalk(profile)

    try:
        layer1.create_application_version(app,
                                          version,
                                          description=version,
                                          s3_bucket=s3_bucket,
                                          s3_key=s3_key)
    except boto.exception.BotoServerError as e:
        io.error(e.message)


def deploy_version(profile, app, version):
    """Deploy application's version in EB."""

    io.info("[profile:%s]" % profile)
    io.echo("Deploy version %s:%s" % (app, version))
    layer1 = get_beanstalk(profile)
    try:
        layer1.update_environment(environment_name=app,
                                  version_label=version)
    except boto.exception.BotoServerError as e:
        io.error(e.message)


def list_versions(profile, app, format_=Format.TEXT):
    """List available application's versions in EB"""

    io.info("[profile:%s]" % profile)
    layer1 = get_beanstalk(profile)
    data = layer1.describe_application_versions(application_name=app)

    versions = (data["DescribeApplicationVersionsResponse"]
                    ["DescribeApplicationVersionsResult"]
                    ["ApplicationVersions"])

    Format.print_list([version["VersionLabel"] for version in versions],
                      format_)


def list_profiles(format_=Format.TEXT):
    """List available user profiles."""

    Format.print_list(get_profile_names(), format_)


def describe_env(profile, app, version=None, format_=Format.TEXT):
    """Describe application's environment variables."""
    if version is None:
        version = app

    Format.print_profile(profile, format_)

    layer1 = get_beanstalk(profile)
    try:
        data = layer1.describe_configuration_settings(application_name=app,
                                                      environment_name=version)
    except boto.exception.BotoServerError as e:
        io.error(e.message)
        return

    env_vars = (data["DescribeConfigurationSettingsResponse"]
                    ["DescribeConfigurationSettingsResult"]
                    ["ConfigurationSettings"]
                    [0]
                    ["OptionSettings"])

    aws_env_var_option = "aws:elasticbeanstalk:application:environment"

    env_vars = {v["OptionName"]: v["Value"] for v in env_vars
                if v["Namespace"] == aws_env_var_option}

    Format.print_dict(env_vars, format_)


def main():
    parser = argparse.ArgumentParser("ebizzle")

    parser.add_argument("-s", "--source-bundle",
                        required=False,
                        help="EB's source bundle location.")
    parser.add_argument("-p", "--profile",
                        required=False,
                        default=DEFAULT_PROFILE,
                        help="AWS CLI profile to use.")
    parser.add_argument("-a", "--all-profiles",
                        required=False,
                        action="store_true",
                        help="Apply for all AWS CLI profiles.")
    parser.add_argument("-f", "--format",
                        required=False,
                        default=Format.TEXT,
                        choices=Format.all(),
                        help="Output format (text or json)")
    parser.add_argument("action", nargs=1,
                        choices=Action.all(),
                        help="Action to perform.")
    parser.add_argument("app", metavar="app:version", nargs="?",
                        help=("Explicitly specify application and version. "
                              "Will try to extract information from the git "
                              "repo in current working dir if not given."))

    args = parser.parse_args()

    action = args.action[0]

    if action == Action.PROFILES:
        list_profiles(args.format)
        return

    try:
        app, version = args.app.split(":")
    except AttributeError:
        app = get_app_name()
        version = get_app_version()
    except ValueError:
        if ":" in args.app:
            raise
        app = args.app

        if action in (Action.LIST, Action.ENV):
            version = None
        else:
            version = get_app_version()

    if args.all_profiles:
        profiles = get_profile_names()
    else:
        profile = args.profile

        if profile not in get_profile_names():
            panic("Profile not found: %s" % profile)

        profiles = [profile]

    if action == Action.CREATE:
        key = upload_source_bundle(profiles[0],
                                   app,
                                   version,
                                   args.source_bundle)
        for profile in profiles:
            create_version(profile,
                           app,
                           version,
                           S3_BUILD_DEPS_BUCKET,
                           key)
    elif action == Action.DEPLOY:
        if args.all_profiles:
            panic("Nope, sorry: won't deploy to all profiles. Not happening. "
                  "Nope.")
        deploy_version(profiles[0], app, version)
    elif action == Action.LIST:
        for i, profile in enumerate(profiles):
            list_versions(profile, app, args.format)
    elif action == Action.ENV:
        for profile in profiles:
            describe_env(profile, app, version, args.format)


if __name__ == "__main__":
    main()

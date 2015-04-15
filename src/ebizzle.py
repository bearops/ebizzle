#!/usr/bin/env python
import os
import sys
import json
import boto
from boto import beanstalk
import argparse
import subprocess
import ConfigParser

import config
import format as fmt
import myio as io


S3_BUILD_DEPS_BUCKET = "dbz-build-deps"

READ_ONLY = False


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


def panic(message=None):
    if message:
        io.error(message)

    sys.exit(1)


def in_git_repository():
    """Is current working dir a git repo?"""

    dev_null = open(os.devnull, "wb")

    return 0 == subprocess.call("git status -s --porcelain",
                                stdout=dev_null,
                                stderr=dev_null,
                                shell=True)


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


def get_s3_conn(profile="production"):
    """Establish and return S3 connection."""

    if profile not in config.get_profile_names():
        profile = config.get_profile_names()[0]

    return boto.connect_s3(*config.get_credentials(profile))


def get_beanstalk(profile):
    """Create and return EB's Layer1."""

    region = beanstalk.regions()[2]
    return beanstalk.layer1.Layer1(*config.get_credentials(profile),
                                   region=region)


def upload_source_bundle(profile, app, version, source_bundle_path,
                         overwrite=False):
    """Upload EB source bundle to S3."""

    fmt.print_profile(profile)
    io.echo("Upload source bundle for %s:%s" % (app, version))

    source_bundle_alt_paths = ["target/%s-%s.zip" % (app, version),
                               "target/source-bundle.zip"]

    if not source_bundle_path:
        io.echo("Source bundle location not given, trying alternative "
                "locations.")
        for alt_path in source_bundle_alt_paths:
            if os.path.isfile(alt_path):
                io.echo("Source bundle found: %s" % alt_path)
                source_bundle_path = alt_path
                break
            else:
                io.echo("Source bundle not found: %s" % alt_path)

    if not source_bundle_path or not os.path.isfile(source_bundle_path):
        panic("Source bundle not found.")

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
        if not READ_ONLY:
            key.set_contents_from_file(f)
        else:
            io.echo("READ ONLY: write %s contents to S3 key."
                    % source_bundle_path)

    return key.key


def create_version(profile, app, version, s3_bucket, s3_key):
    """Create application's version in EB."""

    fmt.print_profile(profile)
    print("Create version %s:%s" % (app, version))
    layer1 = get_beanstalk(profile)

    kwargs = {
        "application_name": app,
        "version_label": version,
        "description": version,
        "s3_bucket": s3_bucket,
        "s3_key": s3_key
    }

    if not READ_ONLY:
        try:
            layer1.create_application_version(**kwargs)
        except boto.exception.BotoServerError as e:
            io.error(e.message)
    else:
        io.echo("READ_ONLY: Create EB application version:")
        for item, value in kwargs.iteritems():
            io.echo("  %s => %s" % (item, value))


def deploy_version(profile, app, version):
    """Deploy application's version in EB."""

    io.info("[profile:%s]" % profile)
    io.echo("Deploy version %s:%s" % (app, version))
    layer1 = get_beanstalk(profile)

    kwargs = {
        "environment_name": app,
        "version_label": version
    }

    if not READ_ONLY:
        try:
            layer1.update_environment(**kwargs)
        except boto.exception.BotoServerError as e:
            io.error(e.message)
    else:
        io.echo("READ_ONLY: Update EB environment:")
        for item, value in kwargs.iteritems():
            io.echo("  %s => %s" % (item, value))


def list_applications(profile, format_=fmt.TEXT):
    """List applications in EB."""

    fmt.print_profile(profile, format_)

    layer1 = get_beanstalk(profile)
    data = layer1.describe_applications()

    apps = (data['DescribeApplicationsResponse']
                ['DescribeApplicationsResult']
                ['Applications'])

    fmt.print_list([app["ApplicationName"] for app in apps], format_)


def list_versions(profile, app, format_=fmt.TEXT):
    """List available application's versions in EB"""

    if app is None:
        return list_applications(profile, format_)

    fmt.print_profile(profile, format_)

    layer1 = get_beanstalk(profile)
    data = layer1.describe_application_versions(application_name=app)

    versions = (data["DescribeApplicationVersionsResponse"]
                    ["DescribeApplicationVersionsResult"]
                    ["ApplicationVersions"])

    fmt.print_list([version["VersionLabel"] for version in versions],
                   format_)


def list_profiles(format_=fmt.TEXT):
    """List available user profiles."""

    fmt.print_list(config.get_profile_names(), format_)


def describe_env(profile, app, version=None, format_=fmt.TEXT):
    """Describe application's environment variables."""

    if version is None:
        version = app

    fmt.print_profile(profile, format_)

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

    fmt.print_dict(env_vars, format_)


def main():
    parser = argparse.ArgumentParser("ebizzle")

    parser.add_argument("-s", "--source-bundle",
                        required=False,
                        help="EB's source bundle location.")

    parser.add_argument("--read-only",
                        action="store_true",
                        required=False,
                        help="Don't make any changes to the infrastructure.")

    profile_group = parser.add_mutually_exclusive_group()
    profile_group.add_argument("-p", "--profile",
                               required=False,
                               default=config.DEFAULT_PROFILE,
                               help="AWS CLI profile to use.")
    profile_group.add_argument("-a", "--all-profiles",
                               required=False,
                               action="store_true",
                               help="Apply for all AWS CLI profiles.")

    parser.add_argument("-f", "--format",
                        required=False,
                        default=fmt.TEXT,
                        choices=fmt.all(),
                        help="Output format (text or json)")

    parser.add_argument("action", nargs=1,
                        choices=Action.all(),
                        help="Action to perform.")

    parser.add_argument("app", metavar="app:version", nargs="?",
                        help=("Explicitly specify application and version. "
                              "Will try to extract information from the git "
                              "repo in current working dir if not given."))

    args = parser.parse_args()

    global READ_ONLY
    READ_ONLY = args.read_only

    action = args.action[0]

    if action == Action.PROFILES:
        list_profiles(args.format)
        return

    try:
        app, version = args.app.split(":")
    except AttributeError:
        app, version = None, None  # panic("App name, messieur?")
    except ValueError:
        if ":" in args.app:
            raise
        app = args.app

        if action in (Action.LIST, Action.ENV):
            version = None
        else:
            version = get_app_version()

    if args.all_profiles:
        profiles = config.get_profile_names()
    else:
        profile = args.profile

        if profile not in config.get_profile_names():
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

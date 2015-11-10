:warning: Deprecated. Please take a look at [ebzl](https://github.com/bearops/ebzl) instead.

# ebizzle

A Python wrapper for AWS ElasticBeanstalk app management.

What can it do?
* Create a new version of your application.
* Deploy an existing version of your application.
* List available versions of your applications.
* List available applications.
* List your application's environment variables.

## Install

```bash
# Activate your preferred virtualenv
git clone https://github.com/dubizzle/ebizzle.git
cd ebizzle
python setup.py install
```

# Config

ebizzle will try to read your AWS profiles from `~/.aws/credentials` and if not
found: `~/.ebizzle/config`.

Config should follow the default AWS credentials syntax:
```
[profile_name]
aws_access_key_id = foo
aws_secret_access_key = bar
```

# Usage

```bash
ebizzle -h
```

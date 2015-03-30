# ebizzle

A Python wrapper for ElasticBeanstalk app management.

What can it do?
* Create a new version of your application.
* Deploy an existing version of your application.
* List available versions of your applications.
* List available applications.
* List your application's environment variables.

# Install

```bash
git clone https://github.com/bearops/ebizzle.git && cd ebizzle && make install
```

A `/usr/local/bin/ebizzle` script will be created in the installation process.

# Config

You'll need a config file holding your AWS credentials in `~/.ebizzle/config`:
```
[profile_name]
aws_access_key_id = foo
aws_secret_access_key = bar
```

# Usage

```bash
ebizzle -h
```

# Change Log

## 2015-05-11
### Fixed
- Installation issue for pip 6.0+

## 2015-05-10
### Changed
- Setup using setuptools thanks to @jeethu

## 2015-05-10
### Changed
- Try to read the config from ~/.aws/credentials first, fallback to ~/.ebizzle/config if that fails.

## 2015-04-23
### Added
- Added `instances` action to list EB env's instances in Ansible inventory format. Example:
  ```
  $ ebizzle instances dubizzleuae-web -pproduction > /etc/ansible/hosts
  $ ansible dubizzleuae-web -m ping
  ```

## 2015-04-15
### Added
- On `create`, if source bundle path was not given, check in `target/source-bundle.zip`.
- Added `--read-only` that prevents ebizzle from performing changes to infrastructure.

# Change Log

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

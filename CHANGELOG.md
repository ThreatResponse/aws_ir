# Change Log
All notable changes to this project will be documented in this file.

## [0.2.2] - 2017-02-26
### Fixed
- Case log S3 upload [#26](https://github.com/ThreatResponse/aws_ir/issues/26)
- `key-compromise` STS token revokation [#24](https://github.com/ThreatResponse/aws_ir/issues/24)

### Changed

- Rename `host-compromise` subcommand to `instance-compromise` [#25](https://github.com/ThreatResponse/aws_ir/issues/25).
- Replace `timesketch_logger` class with python `logging` library [#28](https://github.com/ThreatResponse/aws_ir/issues/28)

## [0.3.0] - 2017-07-20
### Features Added

* Plugin System for Community Plugins
* Pep8 all code base
* Parallel host acquisition
* Support ip address or instance id for targeting
* Separate plugin code to additional python module
* Handle GPG key installation if not present
* Support custom incident plans

### Development Enhancements

* Flake8 in CI Pipeline
* Moto Mocking for Outside-In Test Coverage

## [0.3.1] - 2018-03-10
### CI/CD

* Consolidate Versioning
* Deploy to PyPI from CI for all tagged releases
* Deploy to PyPI test from all untagged releases (adds build # to version)




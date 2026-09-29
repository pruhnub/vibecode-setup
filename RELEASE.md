# Release checklist

## Before the first public release

- [ ] Create the GitHub repository.
- [ ] Verify the package name `vibecode-setup` is available on PyPI.
- [ ] Register a PyPI account and verify email.
- [ ] Create a TestPyPI account separately.
- [ ] Push the repository and confirm CI passes on supported Python versions.
- [ ] Configure a PyPI Trusted Publisher for `.github/workflows/publish.yml`.
- [ ] Optionally configure a TestPyPI Trusted Publisher for a staging workflow.
- [ ] Create a GitHub `pypi` environment for the release workflow.
- [ ] Build both wheel and source distribution locally.
- [ ] Upload to TestPyPI and install from TestPyPI in a clean environment.
- [ ] Test `vibecode init`, `vibecode status`, and `vibecode doctor` after installation.
- [ ] Tag/create a GitHub release matching the package version.
- [ ] Publish the release; GitHub Actions publishes to PyPI via Trusted Publishing.

## Important

Never commit PyPI API tokens to the repository. Trusted Publishing uses GitHub OIDC and short-lived credentials.

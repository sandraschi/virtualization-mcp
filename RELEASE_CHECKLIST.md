# v1.0.0 Release Checklist

## Pre-Release Checks
- [ ] Verify all tests pass
- [ ] Update CHANGELOG.md with release notes
- [ ] Ensure all documentation is up to date
- [ ] Verify DXT packaging works correctly
- [ ] Check for any open issues that should be addressed

## Version Bumping
- [ ] Update `__version__` in `src/vboxmcp/__init__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update version in `dxt_manifest.json`
- [ ] Update any other version references in documentation

## Documentation
- [ ] Verify all documentation is up to date
- [ ] Ensure all new features are documented
- [ ] Update README.md if needed
- [ ] Verify all links in documentation work

## Code Quality
- [ ] Run linters and fix any issues
- [ ] Run type checking
- [ ] Ensure code coverage is adequate
- [ ] Verify all tests pass

## Release Process
- [ ] Create release branch: `release/v1.0.0`
- [ ] Push release branch to GitHub
- [ ] Create pull request to merge into main
- [ ] Run final tests on the release branch
- [ ] Merge pull request into main
- [ ] Create and push git tag: `v1.0.0`
- [ ] Create GitHub release with release notes
- [ ] Upload DXT package to GitHub release
- [ ] Publish to PyPI (if applicable)

## Post-Release
- [ ] Verify GitHub release is complete
- [ ] Test installation from PyPI (if applicable)
- [ ] Update any deployment configurations
- [ ] Announce the release (if needed)
- [ ] Close related issues and milestones

## Verification
- [ ] Verify DXT package installs correctly
- [ ] Verify all features work as expected
- [ ] Check for any immediate issues

## Final Steps
- [ ] Update development version to next planned version
- [ ] Create a new section in CHANGELOG.md for next version
- [ ] Celebrate the release!

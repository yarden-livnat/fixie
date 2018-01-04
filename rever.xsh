$PROJECT = $GITHUB_REPO = 'fixie'
$GITHUB_ORG = 'ergs'

$ACTIVITIES = ['pytest', 'version_bump', 'changelog', 'tag', 'push_tag',
               'pypi', 'conda_forge', 'ghrelease']

$VERSION_BUMP_PATTERNS = [
    ('setup.py', 'VERSION\s*=.*', "VERSION = '$VERSION'"),
    ('fixie/__init__.py', '__version__\s*=.*', "__version__ = '$VERSION'"),
    ]
$CHANGELOG_FILENAME = 'CHANGELOG.rst'
$CHANGELOG_TEMPLATE = 'TEMPLATE.rst'

$DOCKER_CONDA_DEPS = ['xonsh', 'cerberus', 'pytest', 'tornado', 'pytest-tornado', 'lazyasd']
$DOCKER_INSTALL_COMMAND = 'git clean -fdx && ./setup.py install'

$CONDA_FORGE_SOURCE_URL = 'https://pypi.io/packages/source/f/$PROJECT/$PROJECT-$VERSION.tar.gz'

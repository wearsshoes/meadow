# pylint: disable=import-error
from setuptools import setup, find_packages

APP = ['src/meadow/main.py']
DATA_FILES = [
    ('templates', ['src/meadow/web/templates/base.html',
                  'src/meadow/web/templates/viewer.html',
                  'src/meadow/web/templates/settings.html',
                  'src/meadow/web/templates/pdf_upload.html']),
    ('static/css', ['src/meadow/web/static/css/styles.css',
                    'src/meadow/web/static/css/pdf_upload.css']),
    ('static/js', ['src/meadow/web/static/js/settings.js',
                   'src/meadow/web/static/js/sort.js']),
    ('resources', ['src/meadow/resources/icon.png'])
]
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'src/meadow/resources/icon.png',
    'packages': ['rumps', 'PIL', 'anthropic', 'flask', 'fitz'],
    'plist': {
        'LSUIElement': True,  # Makes it a menubar app without dock icon
        'CFBundleName': 'Meadow',
        'CFBundleDisplayName': 'Meadow',
        'CFBundleIdentifier': 'com.meadow.app',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSRequiresAquaSystemAppearance': False,  # Enable dark mode support
    },
}

setup(
    name='meadow',
    version='0.1.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'numpy>=1.26.0',
        'anthropic>=0.37.1',
        'Flask>=3.0.3',
        'Pillow>=11.0.0',
        'pyobjc-framework-Quartz>=10.3.1',
        'rumps>=0.4.0',
        'ptyprocess>=0.7.0',
        'watchdog>=5.0.3',
        'psutil>=6.1.0',
        'PyMuPDF>=1.23.8',  # Added for PDF handling
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'meadow=meadow.main:main',
        ],
    },
    # py2app specific configuration
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

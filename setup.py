"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# Get the long description from the README file
version = "2.7.5"
# Taken from https://stackoverflow.com/questions/14399534/reference-requirements-txt-for-the-install-requires-kwarg-in-setuptools-setup-py/14399775#14399775
with open('requirements.txt') as fp:
    required = fp.read().splitlines()


try:
    # When setuptools_scm is installed, it ignores the MANIFEST.in contents,
    # so a developer won't notice the MANIFEST.in includes are incomplete.
    # This can make some user bugs irrepoducible in a dev environment,
    # and we don't want this!
    # Taken from https://github.com/pypa/setuptools_scm/issues/190#issuecomment-351181286
    import setuptools_scm.integration

    setuptools_scm.integration.find_files = lambda _: []
except ImportError:
    pass

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.


setup(
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    #
    # $ pip install sampleproject
    #
    # And where it will live on PyPI: https://pypi.org/project/sampleproject/
    #
    # There are some restrictions on what makes a valid project name
    # specification here:
    # https://packaging.python.org/specifications/core-metadata/#name
    name='pollenisator-gui',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,  # Required

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description='Pollenisator Client GUI',

    # This is an optional longer description of your project that represents
    # the body of text which users will see when they visit PyPI.
    #
    # Often, this is the same as your README, so you can just read it in from
    # that file directly (as we have already done above)
    #
    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description= """Pollenisator is a tool aiming to assist pentesters and auditor automating the use of some tools/scripts and keep track of them. This a client GUI to Pollenisator project""",  # Optional
    long_description_content_type='text/plain',
    # Denotes that our long_description is in Markdown; valid values are
    # text/plain, text/x-rst, and text/markdown
    #
    # Optional if long_description is written in reStructuredText (rst) but
    # required for plain-text or Markdown; if unspecified, "applications should
    # attempt to render [the long_description] as text/x-rst; charset=UTF-8 and
    # fall back to text/plain if it is not valid rst" (see link below)
    #
    # This field corresponds to the "Description-Content-Type" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-content-type-optional
    # long_description_content_type='text/markdown',  # Optional (see note above)

    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url='https://github.com/AlgoSecure/PollenisatorGUI',  # Optional

    # This should be your name or the name of the organization which owns the
    # project.
    author='AlgoSecure',  # Optional

    # This should be a valid email address corresponding to the author listed
    # above.
    author_email='pollenisator@algosecure.fr',  # Optional

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Topic :: Security',
        'Topic :: System :: Networking :: Monitoring',

        # Pick your license as you wish
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # These classifiers are *not* checked by 'pip install'. See instead
        # 'python_requires' below.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.9',
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords='security tools',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #

    # packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required
   
    packages=find_packages(include=['pollenisatorgui', 'pollenisatorgui.*']),

    # Specify which Python versions you support. In contrast to the
    # 'Programming Language' classifiers above, 'pip install' will check this
    # and refuse to install the project if the version does not match. If you
    # do not support Python 2, you can simplify this to '>=3.5' or similar, see
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires='>=3.7',

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=required,  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    include_package_data=True,
    package_data={  # Optional
        '': ['requirements.txt', ],
		
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],  # Optional

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:

    entry_points={  # Optional
        'console_scripts': [
            'pollenisator-gui=pollenisatorgui.pollenisator:main',
            'pollex=pollenisatorgui.pollex:pollex',
            'pollup=pollenisatorgui.pollenisator:pollup',
            'pollwatch=pollenisatorgui.pollenisator:pollwatch',
            'pollworker=pollenisatorgui.pollworker:pollworker',
            'pollterminal=pollenisatorgui.pollterminal:pollterminal'
        ],
    },

    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/AlgoSecure/PollenisatorGUI/issues',
        # 'Funding': 'https://donate.pypi.org',
        'Source': 'https://github.com/AlgoSecure/PollenisatorGUI/',
    },
)

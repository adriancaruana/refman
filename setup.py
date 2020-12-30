from distutils.core import setup


setup(
  name = 'refman',         # How you named your package folder (MyLib)
  packages = ['refman'],   # Chose the same as "name"
  version = '0.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'RefMan - A Simple python-based reference manager.',   # Give a short description about your library
  author = 'Adrian Caruana',                   # Type in your name
  author_email = 'adrian@adriancaruana.com',      # Type in your E-Mail
  url = 'https://github.com/adriancaruana/refman',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/adriancaruana/refman/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['Reference', 'Manager', 'BibTeX'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'scihub',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3.8',
  ],
)

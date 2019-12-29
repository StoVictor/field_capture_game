from setuptools import setup, find_packages

setup(
    name='field_capture',
    packages=['field_capture'],
    include_package_data=True,
    install_requires=['Flask', 'FlaskWTF',
                      'Flask-SocketIO',
                      'Flask-SQLAlchemy', 'greenlet',
                      'gunicorn', 'MarkupSafe'
                      ],
    extra_require={'test': 'pytest'},
)

import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'mobi_vision'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(include=[package_name, f"{package_name}.*"]),
    data_files=[
        (f'share/{package_name}', ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Add other data files as needed
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Utkarsh',
    maintainer_email='kutkarsh706@gmail.com',
    description='Mobi Vision Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'face_tracking = mobi_vision.face_tracking:main',
            'hand_tracking = mobi_vision.hand_tracking:main',
        ],
    },
)

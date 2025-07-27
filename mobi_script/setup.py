import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'mobi_script'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(include=[package_name, f"{package_name}.*"]),
    data_files=[
        # Install package manifest
        (f'share/{package_name}', ['package.xml']),
        # Ament index marker for rost2-colcon indexing
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        # Launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Utkarsh',
    maintainer_email='kutkarsh706@gmail.com',
    description='Mobi Script Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'task_handler = mobi_script.task_handler:main',
            'undock_action_server = mobi_script.undock_action_server:main',
        ],
    },
)


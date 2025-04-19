from setuptools import find_packages, setup

package_name = 'mobi_speech'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Utkarsh',
    maintainer_email='kutkarsh706@gmail.com',
    description='Mobi Speech Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'voice_conversation = mobi_speech.voice_conversation:main',
        ],
    },
)

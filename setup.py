from setuptools import setup

package_name = 'avatar_ros'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='meganetaaan',
    maintainer_email='ishikawa.s.1027@gmail.com',
    description='This package shows a super-kawaii avatar face',
    license='Apache v2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'avatar_node = avatar_ros.ros_node:main'
        ],
    },
)

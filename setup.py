from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in aumms/__init__.py
from aumms import __version__ as version

setup(
	name="aumms",
	version=version,
	description="AuMMS is an Frappe App to facilitate the Operations in Gold Manufacturing",
	author="efeone",
	author_email="info@efeone.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

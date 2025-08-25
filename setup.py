from setuptools import setup
from setuptools.dist import Distribution
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True
    
class bdist_wheel(_bdist_wheel):
    def get_tag(self):
        # Force python/ABI tag to be generic for all Python 3
        _, _, plat = super().get_tag()
        return ('py3', 'none', plat)

setup(distclass=BinaryDistribution, cmdclass={'bdist_wheel': bdist_wheel})
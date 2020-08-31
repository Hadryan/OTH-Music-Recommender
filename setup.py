from setuptools import setup

setup(name='OTH Music Recommender',
      version='1.0',
      description='A content-based Music Recommender for MPD',
      url='https://github.com/NikoKalbitzer/OTH-Music-Recommender',
      author='Niko Kalbitzer',
      author_email='niko.kalbitzer@st.oth-regensburg.de',
      license='MIT',
      packages=['funniest'],
      install_requires=[
          'tekore','python-mpd2','termcolor', 'scipy.spatial', 'numpy'
      ])
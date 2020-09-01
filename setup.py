import setuptools

setuptools.setup(name='OTH Music Recommender',
                 version='1.0',
                 description='A content-based Music Recommender for MPD',
                 url='https://github.com/NikoKalbitzer/OTH-Music-Recommender',
                 author='Niko Kalbitzer',
                 author_email='niko.kalbitzer@st.oth-regensburg.de',
                 packages=setuptools.find_packages(),
                 install_requires=[
                     'tekore', 'python-mpd2', 'termcolor', 'scipy', 'numpy'
                 ])

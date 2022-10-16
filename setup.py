from setuptools import setup

with open("README.md", 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
   name             =   'hijacked_lib',
   version          =   '0.1',
   description      =   "Hijacked Node's NG text generation and parsing module",
   license          =   "0BSD",
   long_description =   long_description,
   author           =   'Luxter77',
   author_email     =   'Luxter77@eggg.tk',
   url              =   "https://eggg.tk/",
   packages         =   ['hijacked_lib'],
   install_requires =   ['hijacked_log~=0.1', 'numpy~=1.23.4', 'tqdm~=4.64.0'],
   scripts          =   ['scripts/hl-trans-back.py'],
)

python-pkgs:
  pkg.installed:
    - pkgs:
      - python-dev
      - python-pip
    - require:
        - pkg: main-pkgs

/home/vagrant/.pip:
  file.directory:
    - user: vagrant
    - group: vagrant
    - makedirs: True

/home/vagrant/.pip/pip.conf:
  file.managed:
    - source: salt://python/pip.conf
    - user: vagrant
    - group: vagrant
    - require:
        - pkg: python-pkgs
        - file: /home/vagrant/.pip

pip:
  pip.installed:
    - upgrade: True
    - require:
        - pkg: python-pkgs

tox:
  pip.installed:
    - upgrade: True
    - require:
        - pkg: python-pkgs

virtualenv:
  pip.installed:
    - upgrade: True
    - require:
        - pkg: python-pkgs

virtualenvwrapper:
  pip.installed:
    - upgrade: True
    - require:
        - pip: virtualenv

/home/vagrant/.virtualenvs/peps/:
  virtualenv.managed:
    - no_site_packages: True
    - requirements: /vagrant/requirements.txt
    - require:
        - pip: virtualenvwrapper
    - runas: vagrant

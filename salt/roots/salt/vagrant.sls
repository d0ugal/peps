vagrant-pkgs:
  pkg.latest:
    - pkgs:
      - aptitude
      - git-all
      - mercurial
      - psmisc
      - subversion
      - zsh


oh-my-zsh:
  cmd.run:
    - name: 'sudo su -c "wget --no-check-certificate https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | bash" vagrant'
    - runas: vagrant
    - shell: /bin/bash
    - cwd: /home/vagrant
    - require:
      - pkg: vagrant-pkgs

/home/vagrant/.zshrc:
  file.managed:
    - source: salt://vagrant/.zshrc
    - user: vagrant
    - group: vagrant

vagrant:
  user.present:
    - shell: /bin/zsh

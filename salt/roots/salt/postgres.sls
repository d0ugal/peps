postgresql:
  pkg:
    - installed
  service:
    - running

postgresql-pkgs:
  pkg.installed:
    - pkgs:
      - libpq-dev
      - postgresql-server-dev-9.1
      - postgresql-contrib-9.1
    - require:
        - pkg: postgresql

peps-user:
  postgres_user.present:
    - name: peps
    - password: peps
    - runas: postgres
    - superuser: True
    - require:
        - pkg: postgresql-pkgs

peps-db:
  postgres_database.present:
    - name: peps
    - owner: peps
    - runas: postgres
    - require:
        - postgres_user: peps-user

/etc/postgresql/9.1/main/postgresql.conf:
  file.append:
    - text: "listen_addresses = 'localhost'"
    - require:
        - pkg: postgresql-pkgs

/etc/postgresql/9.1/main/pg_hba.conf:
  file:
    - managed
    - source: salt://postgres/pg_hba.conf
    - require:
        - pkg: postgresql-pkgs
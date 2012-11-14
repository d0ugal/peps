
include_recipe "postgresql::default"
include_recipe "postgresql::server_debian"


if node.has_key?("databases")

    node.databases.each do |name, info|

      execute "postgres-createuser-#{info[:username]}" do
          command "sudo -u postgres -- psql -c \"CREATE ROLE #{info[:username]} NOSUPERUSER CREATEDB NOCREATEROLE INHERIT LOGIN PASSWORD \'#{info[:password]}\';\""
          not_if "sudo -u postgres -- psql -c \"SELECT usename FROM pg_user;\" | grep -i #{info[:username]}"
      end

      execute "postgres-createdb-#{name}" do
          command "sudo -u postgres -- createdb -E utf-8 -T template0 --locale=en_US.utf8 -O #{info[:username]} #{name}"
          not_if "sudo -u postgres -- psql -c \"SELECT datname FROM pg_database;\" | grep -i #{name}"
      end

      execute "postgres-hstore-extension" do
        command "sudo -u postgres -- psql #{name} -c \"CREATE EXTENSION IF NOT EXISTS hstore;\""
      end

    end

end
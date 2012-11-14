
execute "move-to-/vagrant" do
  command "echo 'cd /vagrant' >> /home/#{node[:user][:username]}/.bashrc"
  not_if "cat /home/#{node[:user][:username]}/.bashrc | grep vagrant"
end

execute "runserver" do
  command "echo 'alias runserver=\"./manage.py runserver -t 0.0.0.0\"' >> /home/#{node[:user][:username]}/.bashrc"
  not_if "cat /home/#{node[:user][:username]}/.bashrc | grep runserver"
end

node.virtualenvs.each do |name, info|
  execute "run-createdb" do
    command "/home/#{node[:user][:username]}/.virtualenvs/#{name}/bin/python /vagrant/manage.py createdb"
  end
end

node.virtualenvs.each do |name, info|
  execute "run-createdb" do
    command "/home/#{node[:user][:username]}/.virtualenvs/#{name}/bin/python /vagrant/manage.py fetch"
  end
end
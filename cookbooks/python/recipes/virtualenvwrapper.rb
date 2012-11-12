include_recipe "python::pip"
include_recipe "python::virtualenv"

python_pip "virtualenvwrapper" do
  action :install
end

if node.has_key?("user")

  user_info = node[:user]

  execute "source-virtualenvwrapper" do
    command "echo 'source /usr/local/bin/virtualenvwrapper.sh' >> /home/#{user_info[:username]}/.bashrc"
    not_if "cat /home/#{user_info[:username]}/.bashrc | grep virtualenvwrapper"
  end

end
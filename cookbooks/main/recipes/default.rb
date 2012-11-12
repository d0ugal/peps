=begin
  This recipe is a utility recipe, installing a number of additions that are
  useful and required 90% of the time.
=end

execute "update-apt" do
  command "sudo apt-get update"
end

%w{ack-grep aptitude vim git-core libxslt1-dev}.each do |pkg|
  package pkg do
  action :install
  end
end

if node.has_key?("user")

  user_info = node[:user]

  user user_info[:username] do
    shell "/bin/bash"
    supports :manage_home => true
    home "/home/#{user_info[:username]}"
  end

  group user_info[:group] do
    members user_info[:username]
    append true
  end

  if user_info.has_key?("ssh_key")

    directory "/home/#{user_info[:username]}/.ssh" do
      owner user_info[:username]
      group user_info[:group]
      mode 0700
    end

    file "/home/#{user_info[:username]}/.ssh/authorized_keys" do
      owner user_info[:username]
      group user_info[:group]
      mode 0600
      content user_info[:ssh_key]
    end
  end

  directory "/home/#{user_info[:username]}" do
    owner user_info[:username]
    group user_info[:group]
    mode 0775
  end

end

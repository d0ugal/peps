#
# Author:: Seth Chisamore <schisamo@opscode.com>
# Cookbook Name:: python
# Recipe:: virtualenv
#
# Copyright 2011, Opscode, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

include_recipe "python::pip"
include_recipe "python::virtualenv"
include_recipe "python::virtualenvwrapper"

if node.has_key?("user") && node.has_key?("virtualenvs")

  user_info = node[:user]

  script "setup-virtualenv" do
    interpreter "bash"
    user "root"
    cwd "/tmp"
    code "
    mkdir -p /home/#{user_info[:username]}/.virtualenvs
    "
  end

  node.virtualenvs.each do |name, info|

    script "create-virtualenv" do
      interpreter "bash"
      user "root"
      cwd "/tmp"
      code "
      export WORKON_HOME=/home/#{user_info[:username]}/.virtualenvs
      source /usr/local/bin/virtualenvwrapper.sh
      if [ ! -d \"$WORKON_HOME/#{name}\" ]
      then
      mkvirtualenv #{name}
      fi
      "
    end

    if info.has_key?("packages")
      info['packages'].each do |pkg|
        execute "pip-install-#{pkg}" do
          command "/home/#{user_info[:username]}/.virtualenvs/#{name}/bin/pip install #{pkg}"
        end
      end
    end

    if info.has_key?("requirements")
      execute "pip-install-#{info[:requirements]}" do
        command "/home/#{user_info[:username]}/.virtualenvs/#{name}/bin/pip install -r #{info[:requirements]}"
      end
    end

    if info.has_key?("main") && info[:main]
      execute "workon-bashrc" do
        command "echo 'workon #{name}' >> /home/#{user_info[:username]}/.bashrc"
        not_if "cat /home/#{user_info[:username]}/.bashrc | grep workon"
      end
    end

  end

  # chown it all so its not the root user.
  execute "chown-home" do
    command "sudo chown -R #{user_info[:username]} /home/#{user_info[:username]}"
  end

end
Vagrant::Config.run do |config|

  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  config.vm.network :hostonly, "10.10.10.10"

  config.vm.customize ["modifyvm", :id, "--rtcuseutc", "on"]

  config.vm.provision :chef_solo do |chef|

    chef.cookbooks_path = "cookbooks"

    chef.add_recipe "main"
    chef.add_recipe "postgresql::server_debian"
    chef.add_recipe "postgresql::databases"
    chef.add_recipe "python"
    chef.add_recipe "python::virtualenvs"
    chef.add_recipe "dev"

    chef.json.merge!({
      :project_name => "peps",
      :user => {
        :username => "vagrant",
        :group => "user",
      },
      :databases => {
        :pep => {
          :username => "pep",
          :password => "pep",
        }
      },
      :virtualenvs => {
        :pep => {
          :requirements => "/vagrant/requirements/dev.txt",
          :main => true
        }
      }
    })

  end

end
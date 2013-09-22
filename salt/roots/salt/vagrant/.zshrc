# Path to your oh-my-zsh configuration.
ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="candy"

# Set to this to use case-sensitive completion
CASE_SENSITIVE="true"

# Comment this out to disable weekly auto-update checks
# DISABLE_AUTO_UPDATE="true"

# Uncomment following line if you want to disable colors in ls
# DISABLE_LS_COLORS="true"

# Uncomment following line if you want to disable autosetting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment following line if you want red dots to be displayed while waiting for completion
# COMPLETION_WAITING_DOTS="true"

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Example format: plugins=(rails git textmate ruby lighthouse)
plugins=(brew osx git vagrant django pip zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

# Customize to your needs...
export PATH=/usr/local/Cellar/ruby/1.9.3-p392/bin/:/usr/local/bin:/usr/local/sbin:/usr/local/share/python:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/usr/X11/bin:~/bin:/Applications/Hugin/HuginTools

# Setup the history to remove dupes, lines that start with a space.
# Also, make the history HUGE.
export HISTCONTROL=ignoreboth
export HISTSIZE=100000
export HISTIGNORE="[ ]*"

source /usr/local/bin/virtualenvwrapper.sh;


workon peps;
cd /vagrant;
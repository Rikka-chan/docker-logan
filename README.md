Logan Log Viewer
================

![Logan Screenshot](https://raw.githubusercontent.com/jph98/logan/master/logan.png)

Logan is a web based interface real-time log viewer/searcher.

Built upon:
* Python 3.5
* https://raw.githubusercontent.com/jph98/logan/(Jonathan Holloway)

Installation
------------

Install dependencies with:

    sudo pip install flask pyyaml tailer git+https://github.com/Rikka-chan/grin.git
    
Then run:

    ./logagent.py

Configuration
-------------

Look at logagentconfig.yaml:

Specifies the number of lines to display maximum:

    grepnumlines: 250
    
Specifies the number of lines before/after the match to display:

    searchbeforecontext: 2
    searchaftercontext: 2

Specifies the valid extensions for files found in 'directories':

    extensions:
     - log
     - out

To configure the directories to view/search within:

    docker:
      - /var/lib/docker/containers


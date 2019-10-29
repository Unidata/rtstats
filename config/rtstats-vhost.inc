
  # Requires mod-wsgi support!
  # the apache wsgi.conf file should set:
  # WSGIApplicationGroup %{GLOBAL}
  WSGIProcessGroup rtstats_wsgi

  DocumentRoot "/opt/rtstats/htdocs"
  <Directory "/opt/rtstats/htdocs">
  	Order allow,deny
  	Allow from all
  </Directory>

  <Directory "/opt/rtstats/htdocs/services">
    AddHandler wsgi-script .py
    Options +ExecCGI
    RewriteEngine On
    RewriteRule ^idd.geojson(.*) idd.py?service=geojson&$1 [QSA]
    RewriteRule ^idd/(.*).json(.*) idd.py?service=$1$2 [QSA]
    RewriteRule ^hosts.geojson(.*) hosts.py$1 [QSA]
    RewriteRule ^host/(.*)/(.*).json(.*) host.py?hostname=$1&service=$2$3 [QSA]
    RewriteRule ^feedtype/(.*)/(.*).json(.*) feedtype.py?feedtype=$1&service=$2$3 [QSA]
    RewriteRule ^feedtypes.json(.*) feedtypes.py$1 [QSA]
  </Directory>

  <Directory "/opt/rtstats/htdocs/rtstats">
    AddHandler wsgi-script .py
    RewriteEngine On
    RewriteRule ^stats.html stats.php
  </Directory>

  
  ScriptAlias /cgi-bin/ "/opt/rtstats/cgi-bin/"
  <Directory "/opt/rtstats/cgi-bin">
    AddHandler wsgi-script .py
    Options +FollowSymLinks +ExecCGI
    AllowOverride None
    Order allow,deny
	Allow from all
    RewriteEngine On
    RewriteRule ^rtstats/ /cgi-bin/rtstats.py [PT]
  </Directory>
  
  # http://enable-cors.org/server_apache.html
  Header set Access-Control-Allow-Origin "*"
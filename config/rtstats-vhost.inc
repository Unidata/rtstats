  ServerName rtstats.agron.iastate.edu
  ServerAlias rtstats.local
  
  DocumentRoot "/opt/rtstats/htdocs"
  <Directory "/opt/rtstats/htdocs">
  	Order allow,deny
  	Allow from all
  </Directory>

  <Directory "/opt/rtstats/htdocs/services">
    AddHandler cgi-script .py
    Options +ExecCGI
    RewriteEngine On
    RewriteRule ^idd.geojson(.*) idd.py$1 [QSA]
  </Directory>
  ServerName rtstats.agron.iastate.edu
  ServerAlias rtstats.local
  
  DocumentRoot "/opt/rtstats/htdocs"
  <Directory "/opt/rtstats/htdocs">
  	Order allow,deny
  	Allow from all
  </Directory>
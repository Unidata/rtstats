<?php 
require_once "../../phplib/myview.php";
$t = new MyView();
$t->content = <<<EOF
      <h1>Real-Time IDD Statistics</h1>
      <ul>
       <li><a href="/cgi-bin/rtstats/siteindex">Statistics by Host</a></li> 
       <li><a href="/cgi-bin/rtstats/feedindex">Statistics by Feedtype</a></li>
       <li><a href="/cgi-bin/rtstats/topoindex">IDD Topology Maps</a></li>
       <li><a href="/cgi-bin/rtstats/topoindex?tree">IDD Feed Trees</a></li>
      </ul>
EOF;
echo $t->render('main.html');
?>
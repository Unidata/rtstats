<?php 
require_once "../phplib/myview.php";

$t = new MyView();
$t->headextra = <<<EOF
<link rel="stylesheet" href="/vendor/openlayers/3.18.2/ol.css" type="text/css">
<script src="/vendor/openlayers/3.18.2/ol.js"></script>
EOF;
$t->content = <<<EOF

      <h1>Real-Time IDD Statistics</h1>
      <h5>About the IDD</h5>
      <p>The Unidata community of over 260 universities is building a system for disseminating near real-time earth observations via the Internet. Unlike other systems, which are based on data centers where the information can be accessed, Unidata Internet Data Distribution (IDD) is designed so a university can request that certain data sets be delivered to computers at their site as soon as they are available from the observing system. The IDD system also allows any site with access to specialized observations to inject the dataset into the IDD for delivery to other interested sites.  </p>
      <p><a href="http://www.unidata.ucar.edu/projects/index.html#idd" class="more">More information about the IDD</a></p>
      <h5>Real-Time IDD Topology, click line for more information</h5>

<h3>Last Hour: <span id="nbytes">0 TiB</span> transferred by <span id="hosts">0 hosts</span></h3>
<div id="detailfeature"></div>
<br /><strong>View Feedtype:</strong> <select name="ftselect" id="feedtypeselect"></select>
<br /><strong>Latency (minutes) Color Key:
<span style="color: #00ce00;">&lt; 1</span> &nbsp;
<span style="color: #38ff00;">1 to 5</span> &nbsp;
<span style="color: #0091ff;">5 to 30</span> &nbsp;
<span style="color: #00508b;">30 to 60</span> &nbsp;
<span style="color: #ff0000;">&gt;= 60</span> &nbsp;

<div id="map" class="map"></div>
<p><span id="diagnostics"></span></p>
EOF;
$t->footerextra = <<<EOF
<script src="/js/homepage.js"></script>
EOF;

echo $t->render('main.html');
?>

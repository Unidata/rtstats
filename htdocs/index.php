<?php 
require_once "../phplib/myview.php";

$t = new MyView();
$t->headextra = <<<EOF
<link rel="stylesheet" href="/vendor/openlayers/3.18.2/ol.css" type="text/css">
<script src="/vendor/openlayers/3.18.2/ol.js"></script>
EOF;
$t->content = <<<EOF
<h3>Last Hour: <span id="nbytes">0 TiB</span> transferred by <span id="hosts">0 hosts</span></h3>
<div id="detailfeature"></div>
<br /><strong>View Feedtype:</strong> <select name="ftselect" id="feedtypeselect"></select>
<div id="map" class="map"></div>
<p><span id="diagnostics"></span></p>
EOF;
$t->footerextra = <<<EOF
<script src="/js/homepage.js"></script>
EOF;

echo $t->render('main.html');
?>

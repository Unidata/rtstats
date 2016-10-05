var levels = [60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 1, -9999999];
var colors = ['#ff0000', '#ff112c', '#ffaab7', '#97008a', '#9c2bef',
              '#8e67cd', '#00508b', '#0091ff', '#00b3ee', '#00f0ee',
              '#eeed00', '#38ff00', '#00ce00', '#00ce00']

var detailFeature = function(feature){
	$('#detailfeature').html("<strong>" + feature.get("relay") +"</strong>" +
			" to <strong>" + feature.get('node') +"</strong> for LDM Feedtype: TBD" +
			" has latency "+ feature.get('latency') +"s");
}

var styleFunction = function(feature) {
	var geometry = feature.getGeometry();
	var latency = feature.get("latency");
	var color = colors[colors.length - 1];
	for (var i=0; i<(colors.length-1); i++){
		if (latency > levels[i]){
			color = colors[i];
			break;
		}
	}
	var styles = [
	          	// linestring
	          	new ol.style.Style({
	          		stroke : new ol.style.Stroke({
	          			color : color,
	          			width : 2
	          		})
	          	}) ];

	geometry.forEachSegment(function(start, end) {
				var dx = end[0] - start[0];
				var dy = end[1] - start[1];
				var rotation = Math.atan2(dy, dx);
				// arrows
				var svg = '<?xml version="1.0" encoding="utf-8"?><svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" version="1.1"><path style="fill:' + color + ';" d="M 64.00,416.00l 96.00,96.00l 256.00-256.00L 160.00,0.00L 64.00,96.00l 160.00,160.00L 64.00,416.00z" ></path></svg>';
				styles.push(new ol.style.Style(
								{
									geometry : new ol.geom.Point(end),
									image : new ol.style.Icon(
											{
												src : 'data:image/svg+xml;utf8,' + svg,
												anchor : [ 0.75, 0.5 ],
												scale: 0.03,
												color: color,
												rotateWithView : false,
												rotation : -rotation
											})
								}));
			});

	return styles;
};
var raster = new ol.layer.Tile({
	source : new ol.source.OSM()
});
var geojsonSource = new ol.source.Vector({
	format : new ol.format.GeoJSON(),
	projection : ol.proj.get('EPSG:4326'),
	url : '/services/idd.geojson'
});
var geojson = new ol.layer.Vector({
	source : geojsonSource,
	style : styleFunction
});

var map = new ol.Map({
	layers : [ raster, geojson ],
	target : 'map',
	view : new ol.View({
		projection : ol.proj.get('EPSG:3857'),
		center : [ -11000000, 4600000 ],
		zoom : 4
	})
});

map.on('click', function(evt) {
    // console.log('map click() called');
    var pixel = map.getEventPixel(evt.originalEvent);
    var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
        return feature;
    });
    if (feature){
    	detailFeature(feature);
    } 
});

var geojson;
var feedtype = "IDS|DDPLUS";
var levels = [60, 30, 5, 1, -9999999];
var colors = ['#ff0000', '#00508b', '#0091ff', '#38ff00', '#00ce00'];

var detailFeature = function(feature){
	$('#detailfeature').html("<strong><a href=\"/cgi-bin/rtstats/siteindex?" +
			feature.get('relay') +"\">" + feature.get("relay") +"</a></strong>" +
			" to <strong><a href=\"/cgi-bin/rtstats/siteindex?" +
			feature.get('node') + "\">" + feature.get('node') +"</a></strong>" +
			" for LDM Feedtype: " + feedtype +
			" has latency "+ feature.get('latency').toFixed(3) +"s");
}

var loadTopology = function(){
	// manual fetching, since we want to have some access to the GeoJSON data
	// to provide some metadata on this feed to the web UI
	$.ajax({
		url: "/services/idd.geojson?feedtype="+ feedtype,
		dataType: 'json',
		success: function(json){
			geojson.getSource().clear();
			geojson.getSource().addFeatures(
					new ol.format.GeoJSON().readFeatures(json, {
						featureProjection: ol.proj.get('EPSG:3857')
					})
			);
			$("#diagnostics").html("Showing "+ json.count +" feed paths "+
					"generated in " + json['query_time[secs]'].toFixed(2) +
					" seconds valid "+ json["generation_time"]);
		}
	});
}

var styleFunction = function(feature) {
	var geometry = feature.getGeometry();
	var latency = feature.get("latency");
	var color = colors[colors.length - 1];
	for (var i=0; i<(colors.length-1); i++){
		// Latency in feed is expressed in seconds, here we compare with mins
		if ((latency / 60.) > levels[i]){
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

$(function() {

	var raster = new ol.layer.Tile({
		source : new ol.source.OSM()
	});

	geojson = new ol.layer.Vector({
		source: new ol.source.Vector({
			format: new ol.format.GeoJSON(),
			projection : ol.proj.get('EPSG:4326')
		}),
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
		var pixel = map.getEventPixel(evt.originalEvent);
		var feature = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
			return feature;
		});
		if (feature){
			detailFeature(feature);
		} 
	});

	$("#feedtypeselect").change(function(){
		feedtype = $(this).val();
		loadTopology();
	});

	// Populate the Feedtype select widget
	$.ajax({
		url: "/services/feedtypes.json",
		dataType: 'json',
		success: function(json){
			$.each(json['feedtypes'], function(i, value) {
				$('#feedtypeselect').append($('<option>').text(value).attr('value', value));
			});
			$("#feedtypeselect").val(feedtype);
		}
	});

	// Populate the overview
	$.ajax({
		url: "/services/idd/recent.json",
		dataType: 'json',
		success: function(json){
			var data = json['data'][0];
			nbytes = data['nbytes'] / (1024 * 1024 * 1024 * 1024);
			$('#nbytes').html(nbytes.toFixed(3) +" TiB");
			$('#hosts').html(data['hosts'] +" hosts");
		}
	});
	loadTopology();

}); // end of ready()
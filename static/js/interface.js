var mapquery = 'prefLabel';
var mapid = 'uri';
var mapping = { query: mapquery,  id: mapid };

function autointerface(protocol, request, response, cv, mapping) {
    if (!protocol) { protocol = 'skos'; };
    if (protocol == 'skos') {
        return(skosmos(request, response, cv, mapping)); }
    if (protocol == 'example') {
        return(autoexample(request, response)); };
};

function skosmos(request, response, cv, mapping) {
    var result = [];
    var tmp = $.ajax({
        url: cv.cvmReqUrl + '?protocol=skosmos&lang=en&vocab=' + cv.selectedVocab,
        dataType: "json",
        data: { query: request.term },
        success: function(data) {
            var results = data.results;
            var queries = [];
            var array = [];
            $.each(results, function(i, item) {
                queries.push(item.prefLabel);
                array.push({
                    value: item[mapping.query],
                    id: item[mapping.id]
                });
            });

	    response( array );
            console.log( array );
        } 
    })
};

function autoexample (request, response) {
    $.ajax( {
          url: "https://jqueryui.com/resources/demos/autocomplete/search.php",
          dataType: "jsonp",
          data: {
            term: request.term
          },
          success: function( data ) {
            response( data );
            console.log( data );
          }
        } );
};

$(function() {
    $('#tag-search').submit(function(e) {

        var query_string = "";
        var parameters = {'lang': $('#lang').val(),
                          'startdate': $('#startdate').val(),
                          'enddate': $('#enddate').val()}

        for (var item in parameters) {
            if (parameters[item]) {
                if (query_string.length == 0) {
                    separator = "?"
                } else {
                    separator = "&"
                }
                var query_string = query_string + separator + item + "=" + parameters[item]
            }
        }

        var tag = $('#search').val();
	if (tag.indexOf('#') == 0) {
	    tag = tag.substring(1, tag.length);
	}
        window.location.href = '/hashtags/search/' + tag + query_string;
        e.preventDefault();
    });
});

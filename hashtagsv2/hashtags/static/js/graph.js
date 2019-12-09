// Customise chart background colour
var backgroundColor = 'white';
Chart.plugins.register({
    beforeDraw: function(c) {
        var ctx = c.chart.ctx;
        ctx.fillStyle = backgroundColor;
        ctx.fillRect(0, 0, c.chart.width, c.chart.height);
    }
});

url_string = window.location.href;
var url = new URL(url_string);
var project = url.searchParams.get("project");
var user  = url.searchParams.get("user");

// Hide top projects section when filtering on it
if (project!=="" && project!==null){
    $('#top_projects').hide();
}
// Else make an API call and render chart
else{
    $.ajax({
        url: '/api/top_project_stats/?' + url_param,
        dataType: 'json',
        success: function(data){
            var ctx = document.getElementById('projectsChart');
            var projectsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data['projects'],
                    datasets: [{
                        label: 'Number of edits',
                        data: data['edits_per_project'],
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',    
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                callback: function (value) { if (Number.isInteger(value)) { return value; } }
                            }
                        }]
                    },
                    // When chart is rendered, change download and href atribute of anchor 'Download JPG' to allow users to download charts as image
                    // toDataURL function gets url of chart in type of jpeg image
                    animation: { 
                        onComplete: function(){ 
                            let projects_link = document.getElementById("projectsChart").toDataURL("image/jpeg"); 
                            document.getElementById("projects_url").href = projects_link; 
                            document.getElementById("projects_url").setAttribute('download', 'top_projects.jpg'); 
                        } 
                    }
                }
            });
            
            
        },
        complete: function(){
            $('#loader1').hide();
            
        }
    })

}


// Hide top users section when filtering on it 
if (user!=="" && user!==null){
    $('#top_users').hide();
}
// Else make an API call and render chart
else{
    $.ajax({
        url: '/api/top_user_stats/?' + url_param,
        dataType: 'json',
        success: function(data){
            var ctx = document.getElementById('usersChart');
            var projectsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data['usernames'],
                    datasets: [{
                        label: 'Number of edits',
                        data: data['edits_per_user'],
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',    
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                callback: function (value) { if (Number.isInteger(value)) { return value; } }
                            }
                        }]
                    },
                    // When chart is rendered, change download and href atribute of anchor 'Download JPG' to allow users to download charts as image
                    // toDataURL function gets url of chart in type of jpeg image
                    animation: { 
                        onComplete: function(){ 
                            let users_link = document.getElementById("usersChart").toDataURL("image/jpeg"); 
                            document.getElementById("users_url").href = users_link; 
                            document.getElementById("users_url").setAttribute('download', 'top_users.jpg'); 
                        } 
                    }
                }
            });
        },
        complete: function(){
            $('#loader2').hide();
        }
    })
}

$.ajax({
    url: '/api/time_stats/?' + url_param,
    dataType: 'json',
    success: function(data){
        var ctx = document.getElementById('timeChart');
        var timeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data['time_array'],
                datasets: [{
                    label: 'Number of edits',
                    data: data['edits_array'],
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',    
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    fill: false
                }]
            },
            options: {
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true,
                            callback: function (value) { if (Number.isInteger(value)) { return value; } }
                        }
                    }]
                },
                maintainAspectRatio: false,
                // When chart is rendered, change download and href atribute of anchor 'Download JPG' to allow users to download charts as image
                // toDataURL function gets url of chart in type of jpeg image
                animation: { 
                    onComplete: function(){ 
                        let time_link = document.getElementById("timeChart").toDataURL("image/jpeg"); 
                        document.getElementById("time_url").href = time_link; 
                        document.getElementById("time_url").setAttribute('download', 'edits_over_time.jpg'); 
                    } 
                }
            }
        });
    },
    complete: function(){
        $('#loader3').hide();
    }
})
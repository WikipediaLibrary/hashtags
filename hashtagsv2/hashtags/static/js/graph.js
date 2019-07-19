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
            }
        });
    },
    complete: function(){
        $('#loader1').hide();
    }
})
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
            }
        });
    },
    complete: function(){
        $('#loader2').hide();
    }
})
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
                maintainAspectRatio: false
            }
        });
    },
    complete: function(){
        $('#loader3').hide();
    }
})
$(document).ready(function() {
    setTimeout(function(){ 
        $('#network-tab').click(function(event) {
            setTimeout(function(){ 
                window.dispatchEvent(new Event('resize'));
            }, 200);
        });
   }, 5000);
});
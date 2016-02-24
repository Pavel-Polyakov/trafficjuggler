$(document).ready(function(){

  $("a#show_graph").click(function () {
      var name = $(this).data('rel');
      var type = $(this).data('type');
      var description = $(this).data('description');
      var output = $(this).data('output');
      var img = $("#graph");

      $("#info").modal('show');
      $("#spinner").show();

      img.attr('src', type+'/'+name+'.png');
      img.attr('class', 'imagepreview');
      img.css('width', '100%');
      img.load(function() {
              $("#spinner").hide();
      });

      $("#graph_header").text(name);
      $("#graph_description").text(description);
      $("#graph_output").text(output);
  });

})

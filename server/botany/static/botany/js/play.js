(function($) {
  $(".connectfour-col.active").click(function(e) {
    var col = e.target.dataset.connectfourcol;
    $("#game-moves input[name=next_move]").val(col);
    $("#game-moves").submit();
  });
})(jQuery);

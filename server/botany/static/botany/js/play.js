(function($) {
  var maxBoardIx = $(".board").length - 1;
  var currentBoardIx = maxBoardIx;

  function showCurrentBoard() {
    $(".board").hide();
    $(".board").eq(currentBoardIx).show();

    $("#wind-back-to-start").prop("disabled", currentBoardIx == 0)
    $("#wind-back").prop("disabled", currentBoardIx == 0)
    $("#wind-on").prop("disabled", currentBoardIx == maxBoardIx)
    $("#wind-on-to-end").prop("disabled", currentBoardIx == maxBoardIx)
  };

  $("#board-controls > #wind-back-to-start").click(function() {
    currentBoardIx = 0;
    showCurrentBoard();
  });

  $("#board-controls > #wind-back").click(function() {
    if (currentBoardIx == 0) {
      return;
    }
    currentBoardIx -= 1;
    showCurrentBoard();
  });

  $("#board-controls > #wind-on").click(function() {
    if (currentBoardIx == maxBoardIx) {
      return;
    }
    currentBoardIx += 1;
    showCurrentBoard();
  });

  $("#board-controls > #wind-on-to-end").click(function() {
    currentBoardIx = maxBoardIx;
    showCurrentBoard();
  });

  showCurrentBoard();
})(jQuery);

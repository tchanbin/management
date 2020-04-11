$(document).ready(function () {
    $(".nav a").each(function () {
        $this = $(this);
        if ($this[0].href == String(window.location)) {
            $this.parent().addClass("active");
        }
    });
});
$(document).ready(function(){
    $(".one_bar").click(function(){
          $(this).next().slideToggle();
          $(this).parent().siblings().children("ul").slideUp();
    });
});
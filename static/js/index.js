$(document).ready(() => {
    $('#modalDisable').click(function(){
        $('.modal').removeClass('is-active');
        window.location=document.referrer;
    });

    $('.delete').click(function(){
        $('.modal').removeClass('is-active');
        window.location=document.referrer;
    });
});

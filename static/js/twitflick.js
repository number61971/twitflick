// DOM-ready
$(function(){
  // set up ajax spinner
  var spinner = new Spinner({
                      lines:12,
                      length:6,
                      width:3,
                      radius:6,
                      trail:60,
                      speed:1,
                      shadow:false
                    }).spin($('#ajax_spinner')[0]);

  $('#button_twitflick_search')
    .button()
    .click(
      // run the search using ajax instead of POSTing the data to the server
      function(ev){
        $('#ajax_spinner_wrapper').show();
        $.getJSON(
            '/app/twitflick_search_ajax',
            {},
            function(data, textStatus, jqXHR){
              $('#ajax_spinner_wrapper').hide();

              // insert data into the page
              if (data.stat === 'ok') {
                $('#search_count').html(data.search_count);
                $('#search_count_plural').html(data.search_count_plural);
                $('#twitter_search_term').html(data.twitter_search_term);
                $('#twitter_user_link').attr('href', data.twitter_user_url)
                $('#twitter_user_profile_image')
                  .attr('src', data.twitter_user_profile_image_url);
                $('#twitter_user').html(data.twitter_user);
                $('#tweet').html(data.tweet);
                $('#flickr_search_term_display')
                  .html(data.flickr_search_term_display);
                $('#flickr_display').html(data.flickr_display);
              } else {
                alert(data.msg);
              }
            }
          );
        $(this).blur();
        ev.preventDefault();
        });
});

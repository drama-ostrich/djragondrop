
$(function(){

    function getNextContainer(ul_element){
        var container = $(ul_element).closest('.column-container');
        var nextContainer = $(container).next('.column-container');
        return nextContainer;
    }

    function getAllNextContainers(ul_element){
        var container = $(ul_element).closest('.column-container');
        var nextContainers = $(container).nextAll('.column-container');
        return nextContainers;
    }

    function setupColumn(ul_element){ // or a selector for ul elements

        // make it sortable
        $( ul_element ).sortable({
            //stop: function(){}  // could be used to trigger event on drop
            handle:'.drag-handle',
            cursor:'dragging',
            helper:'clone'
        });

        $( ul_element ).draggable({
            revert: "invalid",  // could be used to trigger event on drop
            handle:'.drag-handle',
            cursor:'dragging',
            helper:'clone'
        });

        // disable selection
        $( ul_element ).disableSelection();

    }
    setupColumn(".djragon-column");

    function saveOrder(list){
        // when an item is dropped in the sort order, post the new order
        var items = $(list).sortable("serialize");
        var url = $(list).data('post_url');
        var post = {'items[]': items};
        $.post( url, post )
          .done(function( data ) {
            console.log(data);
          });
    }
    $( "body" ).on( "click", ".djragon-save-order", function() {
        var list = $(this).nextAll('ul.djragon-column');
        saveOrder(list);
    });

    function dropEvent(e, ui){
        var parentPk = $(this).data('pk');
        var childPk = $(ui.draggable).data('pk');
        ui.draggable.remove();
        var url = $(this).data('get_url');
        url += childPk + '/';
        $.post( url )
          .done(function( data ) {
            console.log(data);
          });
    }

    function overEvent(e, ui){
        var callback_this = this;
        window.setTimeout(function(){
            $(callback_this).addClass('drop-over');
            $(ui.helper).addClass('drag-over')
        }, 10)

    }
    function outEvent(e, ui){
        $(this).removeClass('drop-over');
        $(ui.helper).removeClass('drag-over')
    }

    function setupDroppable(li_element){ // or a selector for li elements
        var target = $(li_element).children('i.drop-target');
        $(li_element).droppable({
            accept:'.draggable',
            activeClass: "ui-state-highlight",
            drop: dropEvent,
            over: overEvent,
            out: outEvent

        });
    }

    $( "body" ).on( "click", ".djragon-block", function() {

        // Only the clicked block should be highlighted
        $(this).siblings().removeClass('active');
        $(this).addClass('active');

        var list = $(this).parent(); // where 'this' is the clicked li element
        var nextContainer = getNextContainer(list);
        if (nextContainer.length){  // if there isn't a next container, don't bother.

            // remove draggable and droppable from everything
            $('.draggable').removeClass('draggable');
            $('.djragon-column.ui-draggable').draggable( "destroy" );
            $('.djragon-block.ui-droppable').droppable( "destroy" );

            // only the siblings of this (not this itself) should be droppable
            setupDroppable($(this).siblings());

            // Empty all columns to the right of this one
            var containers = getAllNextContainers(list);
            $(containers).each(function(){$(this).html('');});

            // Popluate the next column with children
            $(nextContainer).html('<span>loading...</span>'); // tell us its loading
            var url = $(this).data('get_url'); // every ul has a data-get_url
            $.get( url )
              .done(function( data ) {
                    $(nextContainer).html(data); // This should return a new ul with a li for each child element
                    var newList = $(nextContainer).children('ul');
                    setupColumn(newList); // set up the ul list we just put in nextContainer
                    var parent_pk = $(newList).data('parent-pk');

                    // add default values to new form
                    var form = newList.prevAll('.djragon-model-form').children('.djragon-form');
                    $(form).find('option').each(function(){
                        console.log($(this).val());
                        if($(this).val() == parent_pk){
                            $(this).attr('selected', 'selected');
                        }
                    });
              });
        }

    });
    $( "body" ).on( "click", ".djangon-open-form", function(){
        if($(this).hasClass('open')){
            $(this).removeClass('open');
            $(this).next('.djragon-model-form').hide();
        }
        else{
            $(this).addClass('open');
            $(this).next('.djragon-model-form').show();
        }

    });
    $("body").on('submit', '.djragon-form', function(e){
        e.preventDefault();
        var callback_this = this;
        var post = $(this).serialize();
        var url = $(this).attr('action');

        $.post( url, post )
          .done(function( data ) {
            var prevContainer = $(callback_this).closest('.column-container').prev('.column-container');
            var activeBlock = $(prevContainer).find('li.djragon-block.active');
            $(activeBlock).click();
          });
    });

    // django CSRF boilerplate
    function getCookie(e){var t=null;if(document.cookie&&""!=document.cookie)for(var o=document.cookie.split(";"),n=0;n<o.length;n++){var r=jQuery.trim(o[n]);if(r.substring(0,e.length+1)==e+"="){t=decodeURIComponent(r.substring(e.length+1));break}}return t}function csrfSafeMethod(e){return/^(GET|HEAD|OPTIONS|TRACE)$/.test(e)}var csrftoken=getCookie("csrftoken");$.ajaxSetup({beforeSend:function(e,t){csrfSafeMethod(t.type)||this.crossDomain||e.setRequestHeader("X-CSRFToken",csrftoken)}});
});


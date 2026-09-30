/*
    *zeon jinhong, 
    *jzee@nemo-c.com,
    *2015 - 02 - 12
*/

(function($){
    $(function(){
        
        $('.login a').mouseenter(function(){
            $(this).stop(true).animate({color:'#ffc056'}, 500);
            $('.login span.login-bg').stop(true).animate({backgroundColor:'#ffc056'}, 500);
        }).mouseleave(function(){
            $(this).stop(true).animate({color:'#b1b1b1'}, 500);
            $('.login span.login-bg').stop(true).animate({backgroundColor:'#b1b1b1'}, 500);
        });

        $('.gnb ul li a').mouseenter(function(){
            $(this).stop(true).animate({color:'#ffc056'}, 500);
        }).mouseleave(function(){
            $(this).stop(true).animate({color:'#ccc'}, 500);
        });

        $('.big-bnlist li a').mouseenter(function(){
            $(this).stop(true).animate({backgroundColor:'#ffe9c5', color:'#fff'}, 600);
        }).mouseleave(function(){
            $(this).stop(true).animate({backgroundColor:'#ffc056', color:'#333'}, 600);
        });

        $('.more_bn a').mouseenter(function(){
            $(this).stop(true).animate({backgroundColor:'#333'}, 600);
        }).mouseleave(function(){
            $(this).stop(true).animate({backgroundColor:'#ffc056'}, 600);
        });

        $('.notice-list li a').mouseenter(function(){
            $(this).animate({color:'#ffc056'}, 500);
        }).mouseleave(function(){
            $(this).animate({color:'#999'}, 500);
        });

        gnbMenu();
		
		$('body').append('<div class="bg_modal"></div>');
        modalpop('login-btn', 'login-modal');

    });
    

    //GNB menu
    function gnbMenu(){
        var speed = 300;
        var delaySpeed = 3000;
        var menuwid = $('.gnb ul>li>a').outerWidth(true);
        var firstwidh = $('.gnb ul>li:eq(0)').children().outerWidth(true);
        $('.gnb .line').css({width:firstwidh});

        $('.gnb ul>li>a').mouseenter(function(){
            var menuidx = $(this).parent().index();
            var thiswid = $(this).outerWidth(true);
            if(menuidx != 0){
                var widnum = 0;
                for(var i=0; i<menuidx; i++){
                    widnum += $('.gnb ul>li').eq(i).outerWidth(true);
                };
                $('.gnb .line').stop(true).animate({left:widnum, width:thiswid}, speed);
            }else{
                $('.gnb .line').stop(true).animate({left:0, width:thiswid}, speed);
            };
        });

        $('.gnb ul').mouseleave(function(){
           var thiswid = $(this).children().eq(0).outerWidth(true);
           $('.gnb .line').delay(delaySpeed).animate({left:0, width:firstwidh}, speed); 
        }).unbind('.gnb ul mouseenter');
    }
	
	function modalpop(handler, target){
		$('.' + handler).click(function(){
			$('.bg_modal').fadeIn(200);
			$('.' + target).delay(200).fadeIn(300);
		});
		$('.' + target).children('.bn-close').children().click(function(){
			$(this).parent().parent().fadeOut(200);
			$('.bg_modal').delay(200).fadeOut(300);
		});
	}

})(jQuery);
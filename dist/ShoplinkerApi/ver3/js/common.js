/*
    *zeon jinhong, 
    *jzee@nemo-c.com,
    *2015 - 02 - 10
*/

(function($){
    $(function(){
		
		//XML tab
		 xmlTab();
		
		//top button
		setTop();

        //GNB Button animation
        $('.gnb>ul>li').mouseenter(function(){
           if($(this).hasClass('ov')){return;}
           $(this).children('a').stop(true).animate({backgroundColor:'#ea9a4c'}, 500);
           $(this).children('span').stop(true).animate({bottom:'55px'}, 200);
        }).mouseleave(function(){
           if($(this).hasClass('ov')){return;}
           $(this).children('a').stop(true).animate({backgroundColor:'#ddb16b'}, 500);
           $(this).children('span').stop(true).animate({bottom:'-30px'}, 200); 
        });
        //logout Button animation
        $('.bn-logout').mouseenter(function(){
            $(this).children('a').animate({backgroundColor:'#1a1714'}, 250, function(){
                $(this).siblings('span').animate({top:'200px'}, 200, function(){
                    $(this).siblings('a').animate({marginTop:'-14px'}, 100);
                });
            });
        }).mouseleave(function(){
            $(this).children('a').animate({backgroundColor:'#2c251b'}, 250, function(){
                $(this).animate({marginTop:'-0'}, 100, function(){
                    $(this).siblings('span').animate({top:'14px'}, 200);
                });
            });
        });
        //2depth Button animation
        $('.menu a').mouseenter(function(){
			if($(this).parent('li').hasClass('ov')){return;}
            $(this).animate({color:'#c48e38'}, 300);
        }).mouseleave(function(){
			if($(this).parent('li').hasClass('ov')){return;}
            $(this).animate({color:'#555'}, 300);
        });
        //tab Button animation
        $('.tabs>li>a').mouseenter(function(){
            if($(this).parent().hasClass('ov')){return;}
            $(this).stop(true).animate({backgroundColor:'#000 ', color:'#b6afa8'}, 300);
        }).mouseleave(function(){
            if($(this).parent().hasClass('ov')){return;}
            $(this).stop(true).animate({backgroundColor:'#312e2b', color:'#8b847d'}, 300);
        });
		
		 //API go button
        $('.big-bn').mouseenter(function(){
            if($(this).parent().hasClass('ov')){return;}
            $(this).css({border:'1px solid #eb9e4c'}).stop(true).animate({backgroundColor:'#eb9e4c ', color:'#fff'}, 300);
        }).mouseleave(function(){
            if($(this).parent().hasClass('ov')){return;}
            $(this).css({border:'1px solid #9a9a9a'}).stop(true).animate({backgroundColor:'#fff', color:'#444', border:'1px solid #9a9a9a'});
        });

        //top Button animation
        $('.bn-top a').mouseenter(function(){
            if($(this).parent().hasClass('ov')){return;}
            $(this).stop(true).animate({backgroundColor:'#000 ', color:'#b6afa8'}, 300);
        }).mouseleave(function(){
            if($(this).parent().hasClass('ov')){return;}
            $(this).stop(true).animate({backgroundColor:'#454240', color:'#9c9288'}, 300);
        });

		 //xml submit
        $('.xml-submit input').mouseenter(function(){
            $(this).stop(true).animate({backgroundColor:'#000 ', color:'#b6afa8'}, 300);
        }).mouseleave(function(){
            $(this).stop(true).animate({backgroundColor:'fff', color:'#666'}, 300);
        });
		
		 //customer Button animation
        $('.bn.custom').mouseenter(function(){
            $(this).stop(true).animate({backgroundColor:'#ffa42d'}, 300);
        }).mouseleave(function(){
            $(this).stop(true).animate({backgroundColor:'#333'}, 300);
        });

    });

	function xmlTab(){
		var speed = 300;
		var $first_cts = $('.tab-cts1').children('li');
		$first_cts.hide();
		$first_cts.eq(0).show();
		$('.xml-tab li').click(function(){
			if(!$('.xml-tab li')) return;
			var idx = $(this).index();
			if($(this).hasClass('ov')) return;
			$(this).siblings('li').removeClass('ov').end().addClass('ov');
			$first_cts.siblings('li').hide().end().eq(idx).fadeIn(speed);
			switch(idx){
				case 1 :
					$('.xml-url').fadeIn(speed);
					$('.testxml-bn').hide();
				break;
				case 2 :
					$('.xml-url').hide();
					$('.testxml-bn').fadeIn(speed);
				break;
				default :
					$('.xml-url').hide();
					$('.testxml-bn').hide();
				break;
			}
		});
	}
	
	function setTop(){
		$('.bn-top').hide();
		$(window).scroll(function(){
			var scroll_location = $(window).scrollTop();
			if(scroll_location >= 80){
				$('.bn-top').fadeIn(500);
			}else if(scroll_location < 80){
				$('.bn-top').fadeOut(500);
			}
		});
		$('.bn-top a').click(function(){
			$('html, body').animate({scrollTop:'0'}, 350);
			return false;
		});
	}

	
	

})(jQuery);


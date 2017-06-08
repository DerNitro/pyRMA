(function ( $, x5engine ) {
	var x = x5engine,
		s = x.settings,
		p = s.currentPath,
		b = x.boot;

	s.siteId = '1393F489FA9E014C05B940ADC16EBFA3';
	s.version = '12-0-3-19';
	b.push(function () {
		x.setupDateTime();
		x.imAccess.showLogout();
		x.utils.autoHeight();
		x.cart.ui.updateWidget();
		x.imGrid.init();
	});
	s.menu = {
		verticalScroll: false,
		orientation: 'horizontal'
	};
	b.push(function () {
		x.menu({
			target: '#imMnMn',
			showCurrent: false,
			desktopVerticalScroll: false,
			mobileVerticalScroll: true,
			showLogoOnScroll: false,
			orientation: 'horizontal',
			menuHeight: 29,
			menuWidth: 140,
			submenuHeight: 33,
			submenuWidth: 170,
			opacity: 0.8,
			type: 'singleColumn',
			alignment: 'left',
			effect: 'fade'
		});
	});
	b.push(function () { x.utils.imPreloadImages([p + 'menu/hor_main.png',p + 'menu/hor_main_h.png',p + 'menu/hor_main_c.png',p + 'menu/sub.png',p + 'menu/sub_h.png',p + 'menu/sub_f.png',p + 'menu/sub_m.png',p + 'menu/sub_l.png',p + 'menu/sub_f_h.png',p + 'menu/sub_m_h.png',p + 'menu/sub_l_h.png', p + 'res/imLoad.gif', p + 'res/imClose.png']); });

	// ShowBox
	$.extend(s.imShowBox, {
		'effect' : 'fade',
		'shadow' : '',
		'background' : '#000000',
		'borderWidth' : {
			'top': 1,
			'right': 1,
			'bottom': 1,
			'left': 1
		},
		'borderRadius' : '3px 3px 3px 3px',
		'borderColor' : '#000000 #000000 #000000 #000000',
		'textColor' : '#000000',
		'fontFamily' : 'Georgia',
		'fontStyle' : 'normal',
		'fontWeight' : 'normal',
		'fontSize' : '9pt',
		'textAlignment' : 'left',
		'boxColor' : '#FFFFFF',
		'opacity' : 0.7,
		'radialBg' : true // Works only in Mozilla Firefox and Google Chrome
	});

	// PopUp
	$.extend(s.imPopUp, {
		'effect' : 'fade',
		'width' : 500,
		'shadow' : '',
		'background' : '#000000',
		'borderRadius' : 10,
		'textColor' : '#000000',
		'boxColor' : '#FFFFFF',
		'opacity' : 0.7
	});

	// Tip
	$.extend(s.imTip, {
		'borderRadius' : 1,
		'arrow' : true,
		'position' : 'bottom',
		'effect' : 'fade',
		'showTail' : true
	});

	// Captcha
	b.push(function () {
		x5engine.captcha.instance = new x5engine.captcha.x5captcha({
			"phpfile": "captcha/x5captcha.php",
		});
	}, false, 'first');

	// BreakPoints
	s.breakPoints.push({ "hash": "fc23f27c1080aa74e1efeec9f2399630", "name": "Desktop", "start": "max", "end": 960, "fluid": false});
	s.breakPoints.push({ "hash": "dec599558301699dfc271392a082819c", "name": "Breakpoint 1", "start": 959, "end": 720, "fluid": false});
	s.breakPoints.push({ "hash": "b5a6e70dcd45b271d4dbff444ddeed77", "name": "Mobile", "start": 719, "end": 480, "fluid": false});
	s.breakPoints.push({ "hash": "e81e7c6a4cc72fa678403ac3f73710af", "name": "Mobile Fluid", "start": 479, "end": 0, "fluid": true});

	b.push(function () { x.cookielaw.activateScripts() });

	s.loaded = true;
})( _jq, x5engine );

<?php require_once("res/x5engine.php"); ?><!DOCTYPE html><!-- HTML5 -->
<html prefix="og: http://ogp.me/ns#" lang="ru-RU" dir="ltr">
	<head>
		<title>Поиск - acs</title>
		<meta charset="utf-8" />
		<!--[if IE]><meta http-equiv="ImageToolbar" content="False" /><![endif]-->
		<meta name="author" content="Sergey Utkin" />
		<meta name="viewport" content="width=device-width, initial-scale=1" />
		<link rel="icon" href="favicon.png?12-0-3-19-636261164936337827" type="image/png" />
		<link rel="stylesheet" type="text/css" href="style/reset.css?12-0-3-19" media="screen,print" />
		<link rel="stylesheet" type="text/css" href="style/print.css?12-0-3-19" media="print" />
		<link rel="stylesheet" type="text/css" href="style/style.css?12-0-3-19" media="screen,print" />
		<link rel="stylesheet" type="text/css" href="style/template.css?12-0-3-19" media="screen" />
		<link rel="stylesheet" type="text/css" href="style/menu.css?12-0-3-19" media="screen" />
		<!--[if lte IE 7]><link rel="stylesheet" type="text/css" href="style/ie.css?12-0-3-19" media="screen" /><![endif]-->
		
		<script type="text/javascript" src="res/jquery.js?12-0-3-19"></script>
		<script type="text/javascript" src="res/x5engine.js?12-0-3-19" data-files-version="12-0-3-19"></script>
		
		
		
		<script type="text/javascript">
			x5engine.boot.push(function () { x5engine.utils.checkBrowserCompatibility(); });
		</script>
		
	</head>
	<body>
		<div id="imHeaderBg"></div>
		<div id="imFooterBg"></div>
		<div id="imPage">
			<div id="imHeader">
				<h1 class="imHidden">Поиск - acs</h1>
				
			</div>
			<a class="imHidden" href="#imGoToCont" title="Заголовок главного меню">Перейти к контенту</a>
			<a id="imGoToMenu"></a><p class="imHidden">Главное меню:</p>
			<div id="imMnMnGraphics"></div>
			<div id="imMnMn" class="auto">
				<div class="hamburger-site-background menu-mobile-hidden"></div><div class="hamburger-button"><div><div><div class="hamburger-bar"></div><div class="hamburger-bar"></div><div class="hamburger-bar"></div></div></div></div><div class="hamburger-menu-background-container"><div class="hamburger-menu-background menu-mobile-hidden"><div class="hamburger-menu-close-button"><span>&times;</span></div></div></div>
				<ul class="auto menu-mobile-hidden">
					<li id="imMnMnNode0" class=" imPage">
						<a href="index.html">
							<span class="imMnMnFirstBg">
								<span class="imMnMnTxt"><span class="imMnMnImg"></span><span class="imMnMnTextLabel">Main</span></span>
							</span>
						</a>
					</li><li id="imMnMnNode5" class=" imLevel">
						<span class="imMnMnFirstBg">
							<span class="imMnMnTxt"><span class="imMnMnImg"></span><span class="imMnMnTextLabel">Admin</span></span>
						</span>
				<ul class="auto">
					</ul></li>
				</ul>
			</div>
			<div id="imContentGraphics"></div>
			<div id="imContent">
				<a id="imGoToCont"></a>
				<h2 id="imPgTitle">Результаты поиска</h2><?php
$search = new imSearch();
$keys = isset($_GET['search']) ? $_GET['search'] : "";
$page = isset($_GET['page']) ? $_GET['page'] : 0;
$type = isset($_GET['type']) ? $_GET['type'] : "pages"; ?>
<div class="searchPageContainer">
<?php echo $search->search($keys, $page, $type); ?>
</div>

				<div class="imClear"></div>
			</div>
			<div id="imFooter">
				
				<div class="imTemplateContent" onclick="x5engine.utils.emailTo('243342','omil.cgma01@kinsut','',''); return false;" style="position: absolute; top: 58px; left: 815px; width: 140px; height: 16px; cursor: pointer;"></div>
				<div id="imFooterResponsiveContent">Copyright 2017. All rights reserved.</div>
			</div>
		</div>
		<span class="imHidden"><a href="#imGoToCont" title="Прочесть эту страницу заново">Назад к содержимому</a> | <a href="#imGoToMenu" title="Прочесть этот сайт заново">Назад к главному меню</a></span>
		
		<noscript class="imNoScript"><div class="alert alert-red">Для использования этого сайта необходимо включить JavaScript.</div></noscript>
	</body>
</html>

<?php
include("../res/x5engine.php");
$nameList = array("cva","y24","ngd","jr4","d4e","35c","mm6","3et","3um","fk4");
$charList = array("5","N","F","Y","P","4","G","P","Y","4");
$cpt = new X5Captcha($nameList, $charList);
//Check Captcha
if ($_GET["action"] == "check")
	echo $cpt->check($_GET["code"], $_GET["ans"]);
//Show Captcha chars
else if ($_GET["action"] == "show")
	echo $cpt->show($_GET['code']);
// End of file x5captcha.php

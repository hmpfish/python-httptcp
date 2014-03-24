<?php
$value = "my cookie value";

if(setcookie("TestCookie",$value,time()+3600)){
    echo "success\n";
}

echo "tet cookie"
?>

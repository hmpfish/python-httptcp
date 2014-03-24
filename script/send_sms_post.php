<?php
date_default_timezone_set ('Asia/Shanghai');

class SendSms
{
	const GATEWAY_TPL = 'http://gateway.woxp.cn:6630/utf8/web_api/';
	# x_eid=0&x_uid=vanchu&x_pwd_md5=8eda0826608e775a386b5646fffd607c&x_ac=10&x_gate_id=300&x_target_no=[MOBILE]&x_memo=[CONTENT]';

	protected function send($mobiles, $content)
	{
		#$contentStr = urlencode($content);
		$contentStr = "$content";

		$url = SendSms::GATEWAY_TPL;
		$post_data=array(
			'x_eid' => '0',
			'x_uid' => 'vanchu',
			'x_pwd_md5' => '8eda0826608e775a386b5646fffd607c',
			'x_ac' => '12',
			'x_gate_id' => '300',
			'x_target_no' => "$mobiles",
			'x_memo' => "$contentStr"
		);

		$ch = curl_init();
		curl_setopt ($ch, CURLOPT_URL, $url);
		curl_setopt ($ch, CURLOPT_RETURNTRANSFER, 1);
		curl_setopt ($ch, CURLOPT_CONNECTTIMEOUT, 5);
		curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
		$file_contents = curl_exec($ch);
		curl_close($ch);
		return $file_contents;
	}

	private function log($mobiles, $status)
	{
		echo '[' . date('Y-m-d H:i:s') . '] ' . $mobiles . ' ' . $status . "\n";
	}

	public function run($mobile, $content)
	{
		$result = $this->send($mobile, $content);
		if($result > 0)
		{
			$this->log($mobile, 'SUCC');
		}
		else
		{
			$this->log($mobile, 'FAILED code=' . $result);
		}
	}
}

if($argc < 3)
	die('usage: php send_sms.php [mobile] [content]' . "\n");
if(strlen($argv[2]) >=449){
	die("Content too long" .$argv[2]. "\n");
}

$app = new SendSms();
$app->run($argv[1], $argv[2]);

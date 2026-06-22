<?php

class AvatarCloudCodeApi
{
    private string $apiBase;
    private array $headers;

    /**
     * 初始化API客户端
     * @param string $baseUrl 接口根地址
     * @param string $apiKey 后台创建的gck_密钥
     */
    public function __construct(string $baseUrl, string $apiKey)
    {
        $this->apiBase = rtrim($baseUrl, '/');
        $this->headers = [
            'X-Api-Key: ' . $apiKey,
            'Content-Type: application/json; charset=utf-8'
        ];
    }

    /**
     * 发送POST请求封装
     */
    private function postRequest(string $path, array $data): array
    {
        $url = $this->apiBase . $path;
        $jsonData = json_encode($data);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $jsonData,
            CURLOPT_HTTPHEADER => $this->headers,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false
        ]);

        $resp = curl_exec($ch);
        $err = curl_error($ch);
        curl_close($ch);

        if ($err) {
            return ['code' => 500, 'msg' => '请求失败:' . $err, 'data' => []];
        }
        return json_decode($resp, true) ?: ['code' => 500, 'msg' => '接口返回数据解析失败', 'data' => []];
    }

    // 1. 随机获取空闲号码
    public function getRandomPhone(int $lockMinute = 5): array
    {
        return $this->postRequest('/get_random_num', ['lock_min' => $lockMinute]);
    }

    // 2. 查询号码验证码
    public function getCodeByPhone(string $phone): array
    {
        return $this->postRequest('/get_code_by_phone', ['phone_number' => $phone]);
    }

    // 3. 释放号码
    public function releasePhone(string $phone): array
    {
        return $this->postRequest('/release_num', ['phone_number' => $phone]);
    }

    // 4. 查询号码状态
    public function getPhoneStatus(string $phone): array
    {
        return $this->postRequest('/num_status', ['phone_number' => $phone]);
    }

    // 5. 批量查询历史验证码
    public function batchHistory(array $phoneList): array
    {
        return $this->postRequest('/batch_history_code', ['phones' => $phoneList]);
    }
}

// ==================== 使用示例 ====================
$API_BASE = "http://127.0.0.1:5000/api/receive_code";
$API_KEY = "gck_4ed779c2874a465145635d238d6f";
$client = new AvatarCloudCodeApi($API_BASE, $API_KEY);

// 1. 取号
$getPhoneRes = $client->getRandomPhone(10);
echo "【随机取号】\n";
var_dump($getPhoneRes);

if ($getPhoneRes['code'] === 200) {
    $phone = $getPhoneRes['data']['phone'];
    // 2. 循环等待验证码
    $verifyCode = '';
    for ($i = 0; $i < 30; $i++) {
        $codeRes = $client->getCodeByPhone($phone);
        if ($codeRes['code'] === 200 && !empty($codeRes['data']['verify_code'])) {
            $verifyCode = $codeRes['data']['verify_code'];
            echo "\n获取验证码：" . $verifyCode . "\n";
            break;
        }
        echo "等待短信...\n";
        sleep(2);
    }

    // 3. 业务完成释放号码
    $releaseRes = $client->releasePhone($phone);
    echo "\n【释放号码结果】\n";
    var_dump($releaseRes);

    // 4. 查询号码状态
    $statusRes = $client->getPhoneStatus($phone);
    echo "\n【号码状态】\n";
    var_dump($statusRes);

    // 5. 批量历史查询
    $batchRes = $client->batchHistory([$phone]);
    echo "\n【批量历史记录】\n";
    var_dump($batchRes);
}
?>
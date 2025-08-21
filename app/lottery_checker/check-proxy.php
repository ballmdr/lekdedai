<?php
// Allow CORS for your WordPress domain
header("Access-Control-Allow-Origin: https://wp-inmotion.ottuat.com");
header("Access-Control-Allow-Origin: https://viu.com");
header("Access-Control-Allow-Origin: https://www.viu.com");
header("Access-Control-Allow-Headers: Content-Type");
header("Access-Control-Allow-Methods: POST, OPTIONS");
header("Access-Control-Allow-Credentials: true");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    // Preflight request
    http_response_code(204);
    exit;
}

$raw = file_get_contents("php://input");
$data = json_decode($raw, true);

if (!$data || !isset($data['number']) || !isset($data['period_date'])) {
    echo json_encode(["error" => "ข้อมูลไม่ครบ"]);
    exit;
}

$apiUrl = "https://www.glo.or.th/api/checking/getcheckLotteryResult";

$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($httpCode !== 200 || !$response) {
    echo json_encode(["error" => "เชื่อมต่อ API ไม่ได้", "details" => $error]);
    exit;
}

echo $response;

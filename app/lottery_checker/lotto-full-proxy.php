<?php
// ✅ Set CORS Headers
$allowed_origins = ['https://wp-inmotion.ottuat.com', 'https://viu.com', 'https://www.viu.com'];
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';

if (in_array($origin, $allowed_origins)) {
    header("Access-Control-Allow-Origin: $origin");
    header("Access-Control-Allow-Credentials: true");
}
header("Access-Control-Allow-Headers: Content-Type");
header("Access-Control-Allow-Methods: POST, OPTIONS");

// ✅ Handle Preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// ✅ Get JSON body
$raw = file_get_contents("php://input");
$data = json_decode($raw, true);

$req_date = $data['date'] ?? null;
$req_month = $data['month'] ?? null;
$req_year = $data['year'] ?? null;

$cacheKey = "lotto_result_{$req_date}_{$req_month}_{$req_year}";

// ✅ Connect to Redis
$redis = new Redis();
try {
    $redis->connect('127.0.0.1', 6379);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(["error" => "Redis connection failed.", "details" => $e->getMessage()]);
    exit;
}

// ✅ Check cache before calling API
$cached = $redis->get($cacheKey);
if ($cached) {
    echo $cached;
    exit;
}

// ✅ Call GLO API if not cached

$apiUrl = "https://www.glo.or.th/api/checking/getLotteryResult";

$payload = [];
if ($req_date && $req_month && $req_year) {
    $payload = [
        "date" => $req_date,
        "month" => $req_month,
        "year" => $req_year
    ];
}

$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
curl_setopt($ch, CURLOPT_TIMEOUT, 10);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($httpCode !== 200 || !$response) {
    http_response_code(500);
    echo json_encode([
        "error" => "Failed to fetch data from GLO API.",
        "details" => $error,
        "httpCode" => $httpCode,
        "apiUrl" => $apiUrl,
        "payload" => $payload
    ]);
    exit;
}

$json = json_decode($response, true);
if (!$json || !is_array($json)) {
    http_response_code(502);
    echo json_encode([
        "error" => "Invalid JSON from GLO API.",
        "raw" => $response
    ]);
    exit;
}

// ✅ ค่อย cache
$redis->setex($cacheKey, 7 * 24 * 60 * 60, $response);


// ✅ Return response
header('Content-Type: application/json');
echo $response;
?>

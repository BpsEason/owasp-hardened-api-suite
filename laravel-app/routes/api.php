<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\ProductController;
use App\Http\Controllers\CommentController;
use Illuminate\Support\Facades\Auth;
use App\Models\User; // 確保導入 User 模型
use Illuminate\Support\Facades\Response;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

// 定義一個自訂的 JSON 響應巨集，用於轉義 JSON 輸出
// 這有助於防止在 JSON 響應中意外輸出未轉義的 HTML 內容，雖然主要防禦應該在數據輸入時完成
Response::macro('jsonEscaped', function ($data, $status = 200, array $headers = [], $options = 0) {
    // 遍歷所有字符串並進行 HTML 實體轉義
    array_walk_recursive($data, function (&$item, $key) {
        if (is_string($item)) {
            $item = e($item);
        }
    });
    return response()->json($data, $status, $headers, $options);
});


// 受保護的路由，需要認證
Route::middleware('auth:sanctum')->group(function () {
    Route::get('/user', function (Request $request) {
        return Response()->jsonEscaped($request->user());
    });

    Route::post('/comments', [CommentController::class, 'store']);
});

// 公開路由
Route::get('/products/{id}', [ProductController::class, 'show']);
Route::get('/products/search', [ProductController::class, 'search']);

// 登入路由
Route::post('/login', function(Request $request) {
    $request->validate([
        'email' => 'required|email',
        'password' => 'required',
    ]);

    if (Auth::attempt($request->only('email', 'password'))) {
        $user = Auth::user();
        // 確保為正確的 Guards 創建 Token，例如 'web' 或 'api' (Laravel 10 預設為 'web')
        // 如果您在 config/auth.php 中有 'sanctum' guard，並且希望為其生成 token，請使用相應的 guard name
        $token = $user->createToken('auth_token')->plainTextToken;
        return Response()->jsonEscaped(['message' => 'Login successful', 'token' => $token]);
    }

    return Response()->jsonEscaped(['message' => 'Invalid credentials'], 401);
});

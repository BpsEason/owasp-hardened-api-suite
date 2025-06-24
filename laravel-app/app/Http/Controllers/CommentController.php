<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Response;
use Illuminate\Support\Str;

class CommentController extends Controller
{
    /**
     * 儲存新評論。
     * 模擬評論提交，並應用 XSS 防禦。
     */
    public function store(Request $request)
    {
        $request->validate([
            'content' => 'required|string|max:1000',
        ]);

        $originalContent = $request->input('content');
        // 使用 Laravel 的 e() 輔助函數進行 HTML 實體轉義，防禦 XSS
        $escapedContent = e($originalContent);

        // 模擬儲存評論到資料庫或處理
        $comment = [
            'id' => (string) Str::uuid(), // 隨機 ID
            'author' => $request->user()->name ?? '匿名用戶', // 假設已認證用戶
            'content' => $escapedContent,
            'timestamp' => now()->toDateTimeString(),
        ];

        return Response::jsonEscaped([
            'message' => 'Comment received!',
            'comment' => $comment,
        ], 201);
    }
}

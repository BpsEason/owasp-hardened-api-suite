<?php

namespace App\Http\Controllers;

use App\Models\Product;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Response; // 導入 Response Facade

class ProductController extends Controller
{
    /**
     * 顯示特定產品的詳情。
     */
    public function show($id)
    {
        $product = Product::find($id);

        if (!$product) {
            return Response::jsonEscaped(['message' => 'Product not found'], 404);
        }

        // 返回 JSON 響應，並確保所有字串都被正確轉義
        return Response::jsonEscaped($product);
    }

    /**
     * 根據名稱或類別搜尋產品。
     */
    public function search(Request $request)
    {
        $query = Product::query();

        if ($request->has('name')) {
            // 使用參數綁定防止 SQL 注入
            $query->where('name', 'like', '%' . $request->input('name') . '%');
        }

        if ($request->has('category')) {
            // 使用參數綁定防止 SQL 注入
            $query->where('category', 'like', '%' . $request->input('category') . '%');
        }

        $products = $query->get();

        // 返回 JSON 響應，並確保所有字串都被正確轉義
        return Response::jsonEscaped($products);
    }
}

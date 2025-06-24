<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Product;

class ProductSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        Product::create([
            'id' => 1,
            'name' => '測試產品 A',
            'description' => '這是一個安全的描述。',
            'price' => 100.00,
            'category' => '電子產品',
        ]);

        Product::create([
            'id' => 2,
            'name' => '測試產品 B',
            'description' => '這是另一個安全的描述。',
            'price' => 200.00,
            'category' => '書籍',
        ]);

        Product::create([
            'id' => 3,
            'name' => '產品 C',
            'description' => '含有 <script>alert("XSS")</script> 的惡意描述',
            'price' => 50.00,
            'category' => '工具',
        ]);

        Product::create([
            'id' => 4,
            'name' => '商品 D',
            'description' => '正常商品',
            'price' => 150.00,
            'category' => '電子產品',
        ]);

        Product::create([
            'id' => 5,
            'name' => '商品 with SQL',
            'description' => 'SELECT * FROM users',
            'price' => 250.00,
            'category' => '數據庫',
        ]);
    }
}

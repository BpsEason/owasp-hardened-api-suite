<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Tests\TestCase;
use App\Models\User;
use Laravel\Sanctum\Sanctum;

class ProductTest extends TestCase
{
    use RefreshDatabase; // 每次測試後刷新資料庫

    /**
     * 設置測試環境。
     */
    protected function setUp(): void
    {
        parent::setUp();
        // 運行資料庫遷移和填充
        $this->artisan('migrate');
        $this->seed();
    }

    /**
     * 測試產品詳情 API 是否返回正確的產品數據。
     */
    public function test_can_retrieve_product_details()
    {
        $response = $this->getJson('/api/products/1');

        $response->assertStatus(200)
                     ->assertJson([
                         'id' => 1,
                         'name' => '測試產品 A',
                     ])
                     ->assertJsonStructure([
                         'id', 'name', 'description', 'price', 'category'
                     ]);
    }

    /**
     * 測試產品詳情 API 是否在產品不存在時返回 404。
     */
    public function test_product_details_not_found()
    {
        $response = $this->getJson('/api/products/999');

        $response->assertStatus(404)
                     ->assertJson([
                         'message' => 'Product not found',
                     ]);
    }

    /**
     * 測試產品搜尋 API 是否可以根據名稱搜尋。
     */
    public function test_can_search_products_by_name()
    {
        $response = $this->getJson('/api/products/search?name=測試產品');

        $response->assertStatus(200)
                     ->assertJsonCount(2)
                     ->assertJsonFragment([
                         'name' => '測試產品 A',
                     ])
                     ->assertJsonFragment([
                         'name' => '測試產品 B',
                     ]);
    }

    /**
     * 測試產品搜尋 API 是否防禦 SQL 注入。
     */
    public function test_product_search_defends_against_sql_injection()
    {
        $response = $this->getJson("/api/products/search?name=' OR 1=1 --");

        $response->assertStatus(200)
                     ->assertJson([]); // 預期不返回任何產品，因為注入被防禦
    }

    /**
     * 測試評論提交 API 是否對 XSS 內容進行轉義（需要認證）。
     */
    public function test_comment_submission_escapes_xss_payload()
    {
        $user = User::factory()->create(); // 使用工廠創建用戶
        Sanctum::actingAs($user); // 模擬用戶認證

        $xssPayload = '<script>alert("XSSed!")</script>';
        $escapedPayload = '&lt;script&gt;alert(&quot;XSSed!&quot;)&lt;/script&gt;'; // 預期的轉義結果

        $response = $this->postJson('/api/comments', ['content' => $xssPayload]);

        $response->assertStatus(201)
                     ->assertJson([
                         'message' => 'Comment received!',
                         'comment' => [
                             'content' => $escapedPayload, // 驗證內容是否被轉義
                         ]
                     ]);

        // 再次確認原始的 XSS payload 不在響應內容中
        $this->assertStringNotContainsString($xssPayload, $response->getContent());
    }

    /**
     * 測試未認證用戶無法提交評論。
     */
    public function test_unauthenticated_user_cannot_submit_comment()
    {
        $response = $this->postJson('/api/comments', ['content' => 'Hello, world!']);

        $response->assertStatus(401)
                 ->assertJson(['message' => 'Unauthenticated.']);
    }
}

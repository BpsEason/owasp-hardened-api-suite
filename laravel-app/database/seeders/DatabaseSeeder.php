<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\User;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // 添加測試用戶
        User::factory()->create([
            'email' => 'test@example.com',
            'password' => bcrypt('password'), // 實際應用中應該使用 Hash::make('password')
        ]);

        $this->call(ProductSeeder::class);
    }
}

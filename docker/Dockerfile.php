FROM php:8.2-fpm-alpine

WORKDIR /var/www/html

# 安裝 PHP 依賴
RUN apk add --no-cache \
    nginx \
    mysql-client \
    curl \
    git \
    unzip \
    libzip-dev \
    supervisor \
    nodejs \
    npm \
    # php-fpm 需要的額外依賴，用於圖片處理等
    libpng-dev \
    libxml2-dev

# 安裝 PHP 擴展
RUN docker-php-ext-install pdo pdo_mysql opcache zip gd mbstring exif pcntl bcmath

# 安裝 Composer
COPY --from=composer:latest /usr/bin/composer /usr/local/bin/composer

# 清理 Composer Cache
RUN composer clear-cache

# 將 PHP-FPM 設定複製到容器中
COPY docker/php-fpm.conf /etc/php8/php-fpm.d/www.conf

# 調整權限
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 775 /var/www/html/storage /var/www/html/bootstrap/cache

EXPOSE 9000

CMD ["php-fpm"]

#!/bin/bash

# 腳本名稱: init.sh
# 目的: 簡化本地開發環境的設置，並增強穩定性和靈活性

set -e # 任何命令失敗時立即退出

PROJECT_NAME="owasp-hardened-api-suite"
COMPOSE_FILE="docker-compose.yml"
LARAVEL_PORT="8000"
FASTAPI_PORT="8001"
ZAP_REPORT_DIR="zap-reports"
REPORT_DIR="reports"

# 顏色代碼，增強輸出可讀性
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 無顏色

# 函數：檢查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}錯誤: 未找到 $1，請先安裝 $1。${NC}"
        exit 1
    fi
}

# 函數：檢查端口是否被佔用
check_port() {
    local port=$1
    if lsof -i :"$port" &> /dev/null; then
        echo -e "${RED}錯誤: 端口 $port 已被佔用，請釋放端口或更改配置。${NC}"
        exit 1
    fi
}

# 函數：檢查服務健康狀態
check_service_health() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}檢查服務 $service 是否就緒...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep "$service" | grep "Up" &> /dev/null; then
            echo -e "${GREEN}服務 $service 已就緒！${NC}"
            return 0
        fi
        echo -e "${YELLOW}等待服務 $service 啟動... ($attempt/$max_attempts)${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e "${RED}錯誤: 服務 $service 未能在 $max_attempts 次嘗試內啟動！${NC}"
    exit 1
}

# 函數：清理舊環境
cleanup_old_environment() {
    echo -e "${YELLOW}清理舊的 Docker 容器和卷...${NC}"
    docker-compose down -v --remove-orphans 2>/dev/null || true
    echo -e "${GREEN}舊環境清理完成。${NC}"
}

# 函數：運行本地安全測試和報告生成
run_security_tests() {
    echo -e "${YELLOW}運行本地安全測試並生成報告...${NC}"
    
    # 運行 PHPUnit 測試
    echo "運行 Laravel PHPUnit 測試..."
    docker-compose exec -T php ./vendor/bin/phpunit --log-junit laravel-report.xml || {
        echo -e "${RED}PHPUnit 測試失敗！${NC}"
        return 1
    }
    if [ -f "laravel-app/laravel-report.xml" ]; then
        mv laravel-app/laravel-report.xml . || {
            echo -e "${RED}移動 PHPUnit 報告失敗！${NC}"
            return 1
        }
    else
        echo -e "${YELLOW}警告: PHPUnit 報告未找到，跳過移動。${NC}"
    fi

    # 運行 Pytest 測試
    echo "運行 FastAPI Pytest 測試..."
    docker-compose exec -T fastapi-tester pytest tests/ --junitxml=pytest-report.xml || {
        echo -e "${RED}Pytest 測試失敗！${NC}"
        return 1
    }
    if [ -f "fastapi-tester/pytest-report.xml" ]; then
        mv fastapi-tester/pytest-report.xml . || {
            echo -e "${RED}移動 Pytest 報告失敗！${NC}"
            return 1
        }
    else
        echo -e "${YELLOW}警告: Pytest 報告未找到，跳過移動。${NC}"
    fi

    # 運行 ZAP 掃描
    echo "運行 OWASP ZAP 掃描..."
    mkdir -p "${ZAP_REPORT_DIR}"
    docker run --rm -v "$(pwd)/${ZAP_REPORT_DIR}:/zap/wrk:rw" owasp/zap2docker-stable \
        zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true &
    sleep 10
    docker run --rm --network="${PROJECT_NAME}_app-network" -v "$(pwd)/${ZAP_REPORT_DIR}:/zap/wrk:rw" owasp/zap2docker-stable \
        zap-cli --port 8080 --host 127.0.0.1 -v \
        openapi "http://nginx:80/api/openapi.json" \
        spider "http://nginx:80/api" \
        active_scan "http://nginx:80/api" \
        report "/zap/wrk/zap_report.json" || true

    # 生成報告
    echo "生成安全報告..."
    docker run --rm -v "$(pwd):/app" python:3.9-slim-buster bash -c \
        "pip install lxml && python /app/scripts/generate_report.py" || {
        echo -e "${RED}報告生成失敗！${NC}"
        return 1
    }

    echo -e "${GREEN}安全報告已生成至 ${REPORT_DIR}/summary.md${NC}"
    return 0
}

# 主流程
echo -e "${GREEN}🚀 正在為 ${PROJECT_NAME} 專案設置本地開發環境...${NC}"

# 1. 檢查環境
echo "檢查系統環境..."
if [ -f ".env" ]; then
    source .env
fi
LARAVEL_PORT=${LARAVEL_PORT:-8000}
FASTAPI_PORT=${FASTAPI_PORT:-8001}
check_command docker
check_command docker-compose
check_port "${LARAVEL_PORT}"
check_port "${FASTAPI_PORT}"

# 2. 可選清理舊環境
if [ "$1" == "--clean" ]; then
    cleanup_old_environment
fi

# 3. 啟動 Docker Compose 服務
echo -e "${YELLOW}🐳 啟動 Docker Compose 服務 (這可能需要一些時間來構建映像)...${NC}"
docker-compose -f "${COMPOSE_FILE}" up --build -d || {
    echo -e "${RED}錯誤: Docker Compose 啟動失敗！請檢查 ${COMPOSE_FILE} 或 Docker 日誌。${NC}"
    exit 1
}

# 4. 檢查服務健康狀態
check_service_health "mariadb"
check_service_health "php"
check_service_health "nginx"
check_service_health "fastapi-tester"

# 5. 初始化 Laravel 應用
echo -e "${YELLOW}✨ 執行 Laravel 應用程式初始化命令...${NC}"

# 安裝 Composer 依賴
echo "📦 安裝 Composer 依賴..."
docker-compose exec -T php composer install --no-dev --optimize-autoloader || {
    echo -e "${RED}Composer 安裝失敗！${NC}"
    exit 1
}

# 生成 Laravel 應用金鑰
echo "🔑 生成 Laravel 應用金鑰..."
docker-compose exec -T php php artisan key:generate --force || {
    echo -e "${RED}應用金鑰生成失敗！${NC}"
    exit 1
}

# 執行資料庫遷移和填充
echo "⚙️ 執行資料庫遷移並填充種子數據..."
docker-compose exec -T php php artisan migrate --seed --force || {
    echo -e "${RED}資料庫遷移或填充失敗！請檢查 MariaDB 服務。${NC}"
    exit 1
}

# 安裝 Laravel Sanctum（僅在必要時執行）
if [ ! -f "laravel-app/config/sanctum.php" ]; then
    echo "🔐 安裝 Laravel Sanctum..."
    docker-compose exec -T php php artisan vendor:publish --provider="Laravel\Sanctum\SanctumServiceProvider" --tag="sanctum-config" || true
else
    echo -e "${YELLOW}Laravel Sanctum 配置已存在，跳過發布。${NC}"
fi

# 6. 可選運行安全測試或顯示日誌
if [ "$1" == "--test" ]; then
    run_security_tests || {
        echo -e "${RED}安全測試或報告生成失敗，請檢查日誌！${NC}"
        exit 1
    }
elif [ "$1" == "--logs" ]; then
    echo -e "${YELLOW}顯示 Docker Compose 日誌...${NC}"
    docker-compose logs -f
fi

# 7. 輸出指引
echo -e "${GREEN}✅ 專案 '${PROJECT_NAME}' 已成功設置！${NC}"
echo ""
echo -e "${YELLOW}🌐 您現在可以通過以下網址訪問應用程式:${NC}"
echo "   Laravel API: http://localhost:${LARAVEL_PORT}/api"
echo "   FastAPI Tester (含 Swagger UI): http://localhost:${FASTAPI_PORT}/docs"
echo ""
echo -e "${YELLOW}🚀 後續步驟:${NC}"
echo "   - 查看所有服務日誌: ./init.sh --logs 或 docker-compose logs -f"
echo "   - 運行 Laravel 測試: docker-compose exec php ./vendor/bin/phpunit"
echo "   - 運行 FastAPI 測試: docker-compose exec fastapi-tester pytest tests/"
echo "   - 運行安全測試並生成報告: ./init.sh --test"
echo "   - 清理並重新設置環境: ./init.sh --clean"
echo "   - 停止所有服務: docker-compose down"
echo ""
echo -e "${YELLOW}📝 注意:${NC}"
echo "   - 確保 Docker 和 Docker Compose 已正確安裝。"
echo "   - 如果遇到問題，請檢查日誌：./init.sh --logs"
echo "   - 報告生成結果位於 ${REPORT_DIR}/summary.md（需使用 --test 選項）。"

# 賦予執行權限
chmod +x init.sh

